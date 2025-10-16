"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/aspose_reader.py
-----------------------------------------------------------------
"""

"""
Aspose.Tasks Reader.
Reads Aspose.Tasks files and converts them to Python Project objects.
"""

import os
import traceback
from typing import Dict, Optional

# --- Aspose Imports ---
try:
    import aspose.tasks as tasks
    print("Info (AsposeReader): 'aspose-tasks' library imported.")
except ImportError:
    # ... (error handling of import) ...
    raise ImportError("Librería 'aspose-tasks' no encontrada.")

# --- Project Core Imports ---
from core.project import Project
from core.entities import Task, Resource
from .base_reader import ProjectReader

class AsposeProjectReader(ProjectReader):
    """
    Aspose.Tasks Reader.
    Version that interprets resource types in a standard way:
    ONLY processes resources of TYPE 0 (Work) to create agents.
    """

    def __init__(self):
        # ... (license if applicable) ...
        pass

    def _get_aspose_cost_per_hour(self, aspose_resource: tasks.Resource) -> float:
        """Tries to get the cost per HOUR of an Aspose resource."""
        try:
            # Direct access to attributes
            std_rate_decimal = aspose_resource.standard_rate
            std_rate_format_enum = aspose_resource.standard_rate_format
            if std_rate_decimal is None or std_rate_format_enum is None: return 0.0
            rate_amount = float(std_rate_decimal)

            # Conversion based on rate format
            if std_rate_format_enum == tasks.RateFormatType.MINUTE: return rate_amount * 60.0
            if std_rate_format_enum == tasks.RateFormatType.HOUR: return rate_amount
            if std_rate_format_enum == tasks.RateFormatType.DAY: return rate_amount / 8.0
            if std_rate_format_enum == tasks.RateFormatType.WEEK: return rate_amount / 40.0
            if std_rate_format_enum == tasks.RateFormatType.MONTH_BY_DAY or \
               std_rate_format_enum == tasks.RateFormatType.MONTH_BY_HOUR: return rate_amount / 160.0
            if std_rate_format_enum == tasks.RateFormatType.YEAR: return rate_amount / 1920.0
            # Ignore cost if it's Material or unhandled type.
            if std_rate_format_enum == tasks.RateFormatType.MATERIAL: return 0.0
            return 0.0 # Default
        except AttributeError: pass # Ignore if cost/rate attributes are missing
        except Exception as e: print(f"Adv (AsposeReader Cost): Exception getting cost/h for Resource ID {getattr(aspose_resource, 'id', 'N/A')}: {e}")
        return 0.0

    def _get_aspose_duration_hours(self, aspose_task: tasks.Task) -> float:
        """Converts an Aspose Duration object to hours."""
        try:
            # Direct access to 'duration' attribute.
            aspose_duration = aspose_task.duration
            if aspose_duration is None: return 0.0
            time_span = aspose_duration.time_span
            if time_span: return time_span.total_hours
            else: # Fallback
                 duration_value = float(aspose_duration.get_value())
                 duration_unit = aspose_duration.time_unit
                 if duration_unit == tasks.TimeUnitType.MINUTE: return duration_value / 60.0
                 if duration_unit == tasks.TimeUnitType.HOUR: return duration_value
                 if duration_unit == tasks.TimeUnitType.DAY: return duration_value * 8.0
                 if duration_unit == tasks.TimeUnitType.WEEK: return duration_value * 40.0
                 return duration_value # Return as is if the unit is not handled.
        except AttributeError: pass # Ignore if duration attribute is missing
        except Exception as e: print(f"Adv (AsposeReader Duration): Exception converting duration to hours for Task UID {getattr(aspose_task, 'unique_id', 'N/A')}: {e}")
        return 0.0

    def load(self, file_path: str) -> Project:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"AsposeReader: File not found: {file_path}")

        print(f"Info (AsposeReader): Loading project from '{file_path}'...")
        project = Project()
        project._clear_project_data()
        resource_map: Dict[int, Resource] = {}
        task_map: Dict[int, Task] = {}

        try:
            prj = tasks.Project(file_path)
            # Get project name
            try: project.project_name = prj.title or os.path.basename(file_path)
            except AttributeError:
                 try: project.project_name = prj.subject or os.path.basename(file_path)
                 except AttributeError: project.project_name = os.path.basename(file_path)

            # --- 1. Process Resources ---
            print(f"Info (AsposeReader): Processing {len(prj.resources)} resources found...")
            resources_processed = 0
            resource_list = list(prj.resources)
            print(f"Info (AsposeReader): Starting iteration over {len(resource_list)} resources...")

            for index, res in enumerate(resource_list):
                res_name = None
                res_id_val = None
                res_type = None
                try:
                    # --- BASIC CHECKS ---
                    if res is None or res.is_null: continue
                    res_id_val = res.id
                    if res_id_val == 0: continue # Skip internal null resource
                    res_name = res.name
                    if res_name is None: continue # Skip resources without name
                    # --- END BASIC CHECKS ---

                    # --- START TYPE CHECK ---
                    # Get the type reported by Aspose
                    res_type = res.type # tasks.ResourceType enum (WORK=0, MATERIAL=1, COST=2)

                    # --- OPTION 1: Correct Logic (ACTIVE NOW) ---
                    # Accepts ONLY resources that Aspose reports as TYPE 0 (Work).
                    if res_type != tasks.ResourceType.WORK: # WORK is 0
                        # print(f"  Debug: Resource ID={res_id_val} is type {res_type}. Skipping (Needs WORK).")
                        continue # Skip if not type Work

                    # --- OPTION 2: Workaround to Accept TYPE 1 (COMMENTED) ---
                    # if res_type != tasks.ResourceType.MATERIAL: # MATERIAL is 1
                    #     continue # Skip if NOT TYPE 1
                    # --- END TYPE CHECK ---


                    # If passes the checks (ID>0, Name not Null, and TYPE=0 according to Aspose), process
                    res_id_int = int(res_id_val)
                    cost_per_hour = self._get_aspose_cost_per_hour(res)

                    # Create the Python resource
                    py_resource = Resource(resource_id=res_id_int, name=res_name, cost_per_hour=cost_per_hour)
                    project.add_resource(py_resource)
                    resource_map[res_id_int] = py_resource

                    resources_processed += 1
                    # Print confirmation
                    print(f"  --> Resource WORK Accepted: ID={res_id_int}, Name='{res_name}', Cost/h={cost_per_hour:.2f} (Total: {resources_processed})")

                except AttributeError as attr_e:
                     print(f"  Adv (AsposeReader): Missing attribute during check/processing of resource index {index}: {attr_e}.")
                     # traceback.print_exc()
                except Exception as res_proc_e:
                     id_str = f"ID={res_id_val}" if res_id_val is not None else "ID?"
                     name_str = f"Name='{res_name}'" if res_name is not None else "Name?"
                     print(f"  Adv (AsposeReader): Error processing resource data {index} ({id_str}, {name_str}): {res_proc_e}")
                     # traceback.print_exc()


            print(f"\nInfo (AsposeReader): End of resource loop. resources_processed = {resources_processed}")
            # Modify error/success message according to the active logic (Option 1)
            if resources_processed == 0:
                 print("Error Critical (AsposeReader): No resources of type WORK (TYPE 0) were loaded.")
                 raise ValueError("Loaded project does not contain valid work resources for simulation.")
            else:
                 print(f"Info (AsposeReader): {resources_processed} work resources processed.")


            # --- 2. Process Tasks and Assignments ---
            # (No changes here)
            print(f"Info (AsposeReader): Processing tasks...")
            tasks_processed = 0
            task_map: Dict[int, Task] = {}

            for tsk in prj.root_task.select_all_children():
                 if tsk is None or tsk.is_null: continue
                 if tsk.is_summary: continue
                 task_unique_id = tsk.unique_id
                 if task_unique_id == 0: continue
                 try:
                     task_uid = int(task_unique_id)
                     task_name = tsk.name or f"Unnamed Task UID {task_uid}"
                     duration_hours = self._get_aspose_duration_hours(tsk)
                     task_cost = float(tsk.cost or 0.0)
                     py_task = Task(task_id=task_uid, name=task_name, duration=duration_hours, estimated_cost=task_cost)
                     assigned_resource_id: Optional[int] = None
                     assignments = list(tsk.assignments)
                     if assignments:
                         for assignment in assignments:
                             if assignment and assignment.resource:
                                 assigned_resource_obj = assignment.resource
                                 if assigned_resource_obj and not assigned_resource_obj.is_null:
                                     assigned_aspose_res_id = int(assigned_resource_obj.id)
                                     if assigned_aspose_res_id != 0:
                                         # Search in our resource_map (which now only has WORK resources)
                                         assigned_py_resource = resource_map.get(assigned_aspose_res_id)
                                         if assigned_py_resource:
                                             assigned_resource_id = assigned_py_resource.id
                                             break
                     py_task.required_resource_id = assigned_resource_id
                     project.add_task(py_task)
                     task_map[task_uid] = py_task
                     tasks_processed += 1
                 except AttributeError as attr_e:
                      print(f"Adv (AsposeReader): Missing attribute in task UID={task_unique_id}: {attr_e}.")
                 except Exception as task_e:
                     error_task_uid_str = f"UID={task_unique_id}" if tsk else "N/A"
                     print(f"Adv (AsposeReader): Error processing Aspose task ({error_task_uid_str}): {task_e}")
                     traceback.print_exc()

            if tasks_processed == 0:
                print("Error Critical (AsposeReader): No valid tasks were loaded.")
                raise ValueError("Loaded project does not contain valid tasks.")
            else:
                print(f"Info (AsposeReader): {tasks_processed} work tasks processed.")


            # --- 3. Process Dependencies ---
            print(f"Info (AsposeReader): Processing {len(prj.task_links)} dependencies...")
            links_processed = 0
            if prj.task_links:
                for link in prj.task_links:
                     if link is None: continue
                     try:
                         link_type = link.link_type
                         pred = link.predecessor
                         succ = link.successor
                         if link_type == tasks.TaskLinkType.FINISH_TO_START:
                             if pred and succ and not pred.is_null and not succ.is_null:
                                 pred_task_uid = int(pred.unique_id)
                                 succ_task_uid = int(succ.unique_id)
                                 if pred_task_uid != 0 and succ_task_uid != 0:
                                     pred_py_task = task_map.get(pred_task_uid)
                                     succ_py_task = task_map.get(succ_task_uid)
                                     if pred_py_task and succ_py_task:
                                         if pred_py_task not in succ_py_task.dependencies:
                                             succ_py_task.dependencies.append(pred_py_task)
                                             links_processed += 1
                     except AttributeError as attr_e:
                          print(f"Adv (AsposeReader): Missing attribute in dependency link: {attr_e}.")
                     except Exception as link_e:
                          pred_id = pred.id if pred else 'N/A'
                          succ_id = succ.id if succ else 'N/A'
                          print(f"Adv (AsposeReader): Error processing dependency ({pred_id} -> {succ_id}): {link_e}")
            print(f"Info (AsposeReader): {links_processed} FS dependencies processed.")


            # --- 4. Finalize and Calculate Baseline ---
            project._calculate_baseline_metrics()
            print(f"Info (AsposeReader): Load completed. Project '{project.project_name}'.")
            print(f"  Tasks: {len(project.tasks)}, Resources: {len(project.resources)}, Planned Base Cost: {project.baseline_cost:.2f}")

        except Exception as e:
            print(f"Error Critical (AsposeReader): Failed to load or process the file '{file_path}': {e}")
            traceback.print_exc()
            raise ValueError(f"AsposeReader: Failed to read or process '{file_path}': {e}")

        return project