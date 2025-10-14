# Contenido completo, final y robusto de core/readers/xml_reader.py

import os
import traceback
from typing import Dict, Optional, Any
from lxml import etree
import isodate

from core.project import ProjectData
from core.entities import Task, Resource
from .base_reader import ProjectReader

XML_RESOURCE_TYPE_WORK = 1
XML_TASK_LINK_TYPE_FS = 1


class XmlProjectReader(ProjectReader):
    """
    Lector de archivos de proyecto en formato XML de Microsoft Project usando lxml.
    Devuelve un objeto ProjectData.
    """

    def _get_namespace(self, element) -> Optional[str]:
        if element.nsmap and None in element.nsmap:
            return element.nsmap[None]
        for ns in element.nsmap.values():
            if 'schemas.microsoft.com/project' in ns:
                return ns
        return None

    def _parse_xml_duration_hours(self, duration_str: Optional[str]) -> float:
        if not duration_str: return 0.0
        try:
            return isodate.parse_duration(duration_str).total_seconds() / 3600.0
        except:
            return 0.0

    def _parse_xml_cost(self, cost_str: Optional[str]) -> float:
        if not cost_str: return 0.0
        try:
            return float(cost_str)
        except:
            return 0.0

    def _parse_xml_cost_per_hour(self, rate_str: Optional[str]) -> float:
        if not rate_str: return 0.0
        try:
            if '/h' in rate_str.lower():
                rate_str = rate_str.lower().replace('/h', '')
            return float(rate_str.strip())
        except:
            return 0.0

    def load(self, file_path: str) -> ProjectData:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"XmlReader: Archivo no encontrado: {file_path}")

        print(f"Info (XmlReader): Loading project from '{file_path}'...")

        tasks: Dict[int, Task] = {}
        resources: Dict[int, Resource] = {}

        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            ns = self._get_namespace(root)
            if not ns: raise ValueError("No se pudo encontrar el namespace principal en el XML.")
            ns_map = {'p': ns}
            print(f"Info (XmlReader): Using namespace: {ns}")

            project_name = root.findtext(f'{{{ns}}}Name', default='Unnamed Project')

            # --- 1. Procesar Recursos ---
            resources_element = root.find(f'{{{ns}}}Resources')
            if resources_element is not None:
                for res_elem in resources_element.findall(f'{{{ns}}}Resource'):
                    res_uid_val = int(res_elem.findtext(f'{{{ns}}}UID'))
                    res_id_val = int(res_elem.findtext(f'{{{ns}}}ID'))
                    res_type_val = int(res_elem.findtext(f'{{{ns}}}Type', default='-1'))

                    if res_type_val != XML_RESOURCE_TYPE_WORK: continue
                    if res_id_val == 0: continue  # Skip resource with ID 0

                    res_name = res_elem.findtext(f'{{{ns}}}Name', default=f"Resource_{res_id_val}")
                    std_rate_elem = res_elem.find(f'{{{ns}}}StandardRate')
                    cost_per_hour = self._parse_xml_cost_per_hour(
                        std_rate_elem.text if std_rate_elem is not None else None)
                    resources[res_id_val] = Resource(resource_id=res_id_val, name=res_name, cost_per_hour=cost_per_hour)

            # --- 2. Procesar Tareas ---
            tasks_element = root.find(f'{{{ns}}}Tasks')
            if tasks_element is not None:
                for task_elem in tasks_element.findall(f'{{{ns}}}Task'):
                    is_summary = task_elem.findtext(f'{{{ns}}}Summary') == '1'
                    task_uid_val_text = task_elem.findtext(f'{{{ns}}}UID')
                    if is_summary or task_uid_val_text is None: continue
                    task_uid_val = int(task_uid_val_text)
                    if task_uid_val == 0: continue

                    task_name = task_elem.findtext(f'{{{ns}}}Name', default=f"Task_{task_uid_val}")
                    dur_str = task_elem.findtext(f'{{{ns}}}Duration')
                    duration_hours = self._parse_xml_duration_hours(dur_str)
                    cost_str = task_elem.findtext(f'{{{ns}}}Cost')
                    task_cost = self._parse_xml_cost(cost_str)
                    tasks[task_uid_val] = Task(task_id=task_uid_val, name=task_name, duration=duration_hours,
                                               estimated_cost=task_cost)

            # --- 3. Procesar Asignaciones ---
            assignments_element = root.find(f'{{{ns}}}Assignments')
            if assignments_element is not None:
                for assign_elem in assignments_element.findall(f'{{{ns}}}Assignment'):
                    task_uid_text = assign_elem.findtext(f'{{{ns}}}TaskUID')
                    res_id_text = assign_elem.findtext(
                        f'{{{ns}}}ResourceUID')  # Esto es en realidad Resource *ID* en muchos XML
                    if task_uid_text and res_id_text:
                        task_uid = int(task_uid_text)
                        res_id = int(res_id_text)
                        if task_uid in tasks and res_id in resources:
                            tasks[task_uid].required_resource_id = res_id

            # --- 4. Procesar Dependencias ---
            dependency_elements = root.findall('.//p:PredecessorLink', ns_map)
            print(f"Info (XmlReader): Processing {len(dependency_elements)} dependencies...")
            for link in dependency_elements:
                pred_uid_text = link.findtext('p:PredecessorUID', namespaces=ns_map)
                succ_uid_text = link.findtext('p:SuccessorUID', namespaces=ns_map)
                link_type_text = link.findtext('p:Type', default='0', namespaces=ns_map)

                # MODIFIED: Added a check to ensure values exist
                if pred_uid_text is None or succ_uid_text is None:
                    continue  # Skip this link if incomplete

                # If values exist, convert them to numbers
                pred_uid = int(pred_uid_text)
                succ_uid = int(succ_uid_text)
                link_type = int(link_type_text)

                if link_type == XML_TASK_LINK_TYPE_FS and succ_uid in tasks and pred_uid in tasks:
                    tasks[succ_uid].dependencies.append(pred_uid)

            # --- 5. Finalizar y Devolver ProjectData ---
            baseline_cost = sum(t.estimated_cost for t in tasks.values())
            project_data = ProjectData(project_name, tasks, resources, baseline_cost)
            print(f"Info (XmlReader): Load completed. Returning ProjectData.")
            return project_data

        except Exception as e:
            print(f"Critical Error (XmlReader): Failed to load XML file '{file_path}': {e}")
            traceback.print_exc()
            raise ValueError(f"XmlReader: Failed to read or process '{file_path}'.")