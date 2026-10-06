"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/xml_reader.py
-----------------------------------------------------------------
"""

"""
XML Reader.
Reads XML files and converts them to Python Project objects.
"""

import os
from typing import Dict, List, Optional, Tuple
from lxml import etree
import isodate

from core.project import ProjectData
from core.entities import Task, Resource
from core.exceptions import ReaderError
from .base_reader import ProjectReader

XML_RESOURCE_TYPE_WORK = 1
XML_TASK_LINK_TYPE_FS = 1


class XmlProjectReader(ProjectReader):
    """
    Reads XML files of Microsoft Project and converts them to Python Project objects.
    Returns a ProjectData object.

    Effort comes from each task's <Work>; tasks without a <Work> element fall back to <Duration>.
    Invalid values raise ReaderError instead of being silently replaced.
    """

    supported_extensions = ['xml']

    def _get_namespace(self, element) -> Optional[str]:
        if element.nsmap and None in element.nsmap:
            return element.nsmap[None]
        for ns in element.nsmap.values():
            if 'schemas.microsoft.com/project' in ns:
                return ns
        return None

    def _parse_xml_duration_hours(self, duration_str: Optional[str], where: str = "") -> float:
        if not duration_str: return 0.0
        try:
            return isodate.parse_duration(duration_str).total_seconds() / 3600.0
        except (isodate.ISO8601Error, ValueError) as e:
            raise ReaderError(f"Invalid duration '{duration_str}' {where}".strip(),
                              value=duration_str) from e

    def _parse_xml_cost(self, cost_str: Optional[str], where: str = "") -> float:
        if not cost_str: return 0.0
        try:
            return float(cost_str)
        except ValueError as e:
            raise ReaderError(f"Invalid cost '{cost_str}' {where}".strip(), value=cost_str) from e

    def _parse_xml_cost_per_hour(self, rate_str: Optional[str], where: str = "") -> float:
        if not rate_str: return 0.0
        try:
            if '/h' in rate_str.lower():
                rate_str = rate_str.lower().replace('/h', '')
            return float(rate_str.strip())
        except ValueError as e:
            raise ReaderError(f"Invalid rate '{rate_str}' {where}".strip(), value=rate_str) from e

    def _parse_int(self, text: Optional[str], where: str) -> int:
        try:
            return int(text)
        except (TypeError, ValueError) as e:
            raise ReaderError(f"Invalid or missing integer '{text}' {where}", value=text) from e

    def load(self, file_path: str) -> ProjectData:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"XmlReader: File not found: {file_path}")

        print(f"Info (XmlReader): Loading project from '{file_path}'...")

        try:
            root = etree.parse(file_path).getroot()
        except etree.XMLSyntaxError as e:
            raise ReaderError(f"Malformed XML in '{file_path}': {e}") from e

        ns = self._get_namespace(root)
        if not ns:
            raise ReaderError(f"No MS Project namespace found in '{file_path}'.")
        print(f"Info (XmlReader): Using namespace: {ns}")
        q = lambda tag: f'{{{ns}}}{tag}'

        project_name = root.findtext(q('Name'), default='Unnamed Project')

        # --- 1. Process Resources (keyed by ID; assignments refer to UID) ---
        resources: Dict[int, Resource] = {}
        resource_uid_to_id: Dict[int, int] = {}
        resources_element = root.find(q('Resources'))
        if resources_element is not None:
            for res_elem in resources_element.findall(q('Resource')):
                res_uid_val = self._parse_int(res_elem.findtext(q('UID')), "in Resource UID")
                res_id_val = self._parse_int(res_elem.findtext(q('ID')), f"in ID of resource UID {res_uid_val}")
                res_type_val = int(res_elem.findtext(q('Type'), default='-1'))

                if res_type_val != XML_RESOURCE_TYPE_WORK: continue
                if res_id_val == 0: continue  # Skip resource with ID 0 (not a valid resource)

                res_name = res_elem.findtext(q('Name'), default=f"Resource_{res_id_val}")
                cost_per_hour = self._parse_xml_cost_per_hour(
                    res_elem.findtext(q('StandardRate')), f"for resource {res_id_val}")
                resources[res_id_val] = Resource(resource_id=res_id_val, name=res_name, cost_per_hour=cost_per_hour)
                resource_uid_to_id[res_uid_val] = res_id_val

        # --- 2. Process Tasks and their predecessor links ---
        tasks: Dict[int, Task] = {}
        predecessor_links: List[Tuple[int, int, int]] = []  # (successor_uid, predecessor_uid, link_type)
        lagged_links = 0
        tasks_element = root.find(q('Tasks'))
        if tasks_element is not None:
            for task_elem in tasks_element.findall(q('Task')):
                is_summary = task_elem.findtext(q('Summary')) == '1'
                task_uid_val_text = task_elem.findtext(q('UID'))
                if is_summary or task_uid_val_text is None: continue
                task_uid_val = self._parse_int(task_uid_val_text, "in Task UID")
                if task_uid_val == 0: continue

                where = f"in task {task_uid_val}"
                task_name = task_elem.findtext(q('Name'), default=f"Task_{task_uid_val}")
                duration_hours = self._parse_xml_duration_hours(task_elem.findtext(q('Duration')), where)
                work_str = task_elem.findtext(q('Work'))
                work_hours = self._parse_xml_duration_hours(work_str, where) if work_str else None
                task_cost = self._parse_xml_cost(task_elem.findtext(q('Cost')), where)
                tasks[task_uid_val] = Task(task_id=task_uid_val, name=task_name, duration=duration_hours,
                                           estimated_cost=task_cost, work=work_hours)

                # In MS Project XML the link lives inside the successor task
                for link in task_elem.findall(q('PredecessorLink')):
                    pred_uid = self._parse_int(link.findtext(q('PredecessorUID')), f"in PredecessorLink {where}")
                    link_type = int(link.findtext(q('Type'), default=str(XML_TASK_LINK_TYPE_FS)))
                    predecessor_links.append((task_uid_val, pred_uid, link_type))
                    if link.findtext(q('LinkLag'), default='0') not in ('0', ''):
                        lagged_links += 1

        # --- 3. Process Assignments (primary resource = the one with the most work) ---
        assignments_by_task: Dict[int, List[Tuple[float, int]]] = {}
        assignments_element = root.find(q('Assignments'))
        if assignments_element is not None:
            for assign_elem in assignments_element.findall(q('Assignment')):
                task_uid_text = assign_elem.findtext(q('TaskUID'))
                res_uid_text = assign_elem.findtext(q('ResourceUID'))
                if not task_uid_text or not res_uid_text:
                    continue
                task_uid = self._parse_int(task_uid_text, "in Assignment TaskUID")
                res_id = resource_uid_to_id.get(self._parse_int(res_uid_text, "in Assignment ResourceUID"))
                if task_uid in tasks and res_id is not None:
                    assign_work = self._parse_xml_duration_hours(
                        assign_elem.findtext(q('Work')), f"in assignment of task {task_uid}")
                    assignments_by_task.setdefault(task_uid, []).append((assign_work, res_id))

        multi_resource_tasks = []
        for task_uid, assignments in assignments_by_task.items():
            task = tasks[task_uid]
            # max() keeps the first assignment on ties
            task.required_resource_id = max(assignments, key=lambda a: a[0])[1]
            if len(assignments) > 1:
                task.set_metadata('assigned_resource_ids', [res_id for _, res_id in assignments])
                multi_resource_tasks.append(task_uid)
        if multi_resource_tasks:
            print(f"Warning (XmlReader): {len(multi_resource_tasks)} task(s) have several resources; "
                  f"only the one with the most work is simulated: {multi_resource_tasks}")

        # --- 4. Resolve dependencies (Project converts these IDs to Task objects) ---
        skipped_type, skipped_missing = 0, 0
        dependency_ids: Dict[int, List[int]] = {}
        for succ_uid, pred_uid, link_type in predecessor_links:
            if link_type != XML_TASK_LINK_TYPE_FS:
                skipped_type += 1
            elif pred_uid not in tasks:
                skipped_missing += 1
            else:
                dependency_ids.setdefault(succ_uid, []).append(pred_uid)
        for succ_uid, pred_uids in dependency_ids.items():
            tasks[succ_uid].dependencies = pred_uids
        print(f"Info (XmlReader): Loaded {sum(map(len, dependency_ids.values()))} of "
              f"{len(predecessor_links)} dependencies.")
        if skipped_type:
            print(f"Warning (XmlReader): {skipped_type} non finish-to-start link(s) ignored.")
        if skipped_missing:
            print(f"Warning (XmlReader): {skipped_missing} link(s) to summary or unknown tasks ignored.")
        if lagged_links:
            print(f"Warning (XmlReader): {lagged_links} link(s) have a lag or lead; lags are ignored "
                  f"(the successor starts as soon as the predecessor finishes).")

        # --- 5. Finalize and Return ProjectData ---
        baseline_cost = sum(t.estimated_cost for t in tasks.values())
        print(f"Info (XmlReader): Load completed. Returning ProjectData.")
        return ProjectData(project_name, tasks, resources, baseline_cost)
