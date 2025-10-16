"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/mpxj_reader.py
-----------------------------------------------------------------
"""

"""
MPXJ Reader.
Reads MPXJ files and converts them to Python Project objects.
"""

import os
from typing import Dict, Optional, Tuple
import jpype
import jpype.imports
from jpype.types import JString
import traceback

from core.project import Project
from core.entities import Task, Resource
from .base_reader import ProjectReader

_mpxj_reader_instance = None
_jvm_started = False

MPXJ_JAR_PATH = os.environ.get("MPXJ_JAR", r"C:\path\to\your\library\mpxj-10.x.x.jar") # <-- ADJUST THIS PATH!!

def _start_jvm(jar_path: str):
    global _jvm_started
    if _jvm_started: return
    if not os.path.exists(jar_path):
        raise FileNotFoundError(f"MPXJ JAR not found at: {jar_path}. Check MPXJ_JAR environment variable or path in mpxj_reader.py.")

    try:
        if not jpype.isJVMStarted():
            print(f"Info (MPXJ): Starting JVM with JAR: {jar_path}...")
            jpype.startJVM(classpath=[jar_path], convertStrings=False)
            _jvm_started = True
            print("Info (MPXJ): JVM started.")
        else:
            _jvm_started = True
            print("Info (MPXJ): JVM was already started.")
    except Exception as e:
        print(f"Critical Error (MPXJ): Could not start JVM: {e}")
        traceback.print_exc()
        _jvm_started = False
        raise RuntimeError(f"Failed to start JVM for MPXJ: {e}")

class MpxjProjectReader(ProjectReader):
    def __init__(self, mpxj_jar_path: str = MPXJ_JAR_PATH):
        self.jar_path = mpxj_jar_path
        _start_jvm(self.jar_path)
        try:
            jpype.imports.load_java_packages()
            from net.sf.mpxj.reader import UniversalProjectReader
            from net.sf.mpxj import TaskField, ResourceField, Duration, ProjectFile, ResourceAssignment, Rate
            # NEW: Classes for resources and assignments
            from net.sf.mpxj import Resource as MpxjResource # Rename to avoid conflict
            from net.sf.mpxj.common import TimeUnit

            self.MPXJUniversalReader = UniversalProjectReader
            self.MPXJTaskField = TaskField
            self.MPXJResourceField = ResourceField
            self.MPXJDuration = Duration
            self.MPXJTimeUnit = TimeUnit # NEW
            self.MpxjResource = MpxjResource # NEW
            self.MPXJRate = Rate # NEW

            print("Info (MPXJReader): Java MPXJ classes imported.")
        except ImportError as e:
            print(f"Critical Error (MPXJReader): Could not import MPXJ classes via JPype: {e}")
            traceback.print_exc()
            raise RuntimeError("Failed to import MPXJ classes.")
        except Exception as e: # Capture general errors from JPype/JVM
            print(f"Critical Error (MPXJReader): Unexpected error during MPXJ classes import: {e}")
            traceback.print_exc()
            raise RuntimeError(f"Failed during MPXJReader initialization: {e}")

    def _get_cost_per_hour(self, mpxj_resource: 'MpxjResource') -> float:
        """Try to get the cost per hour of an MPXJ resource."""
        try:
            std_rate: Optional['Rate'] = mpxj_resource.getStandardRate()
            if std_rate is not None:
                # MPXJ returns the cost in the specified time unit (e.g. /h, /d).
                rate_amount = float(std_rate.getAmount())
                rate_units = std_rate.getTimeUnits()

                if rate_units == self.MPXJTimeUnit.HOURS:
                    return rate_amount
                elif rate_units == self.MPXJTimeUnit.MINUTES:
                    return rate_amount * 60.0
                elif rate_units == self.MPXJTimeUnit.DAYS:
                    # Assume 8 hours per day if no specific info
                    hours_per_day = 8.0 # Could be read from project calendar options
                    return rate_amount / hours_per_day
                elif rate_units == self.MPXJTimeUnit.WEEKS:
                    hours_per_week = 40.0 # Assume 40 hours/week
                    return rate_amount / hours_per_week
                # Add more conversions if necessary (months, years)
                else:
                    print(f"Adv (MPXJReader): Unhandled rate unit '{rate_units}' for Resource ID {mpxj_resource.getID()}. Using rate as is.")
                    return rate_amount # Return without converting if the unit is unknown
            else:
                 # Try to get from Cost field if StandardRate is not available
                 cost_val = mpxj_resource.getCost()
                 if cost_val is not None:
                     # Warning: This 'Cost' field may not be per hour.
                     print(f"Adv (MPXJReader): Resource ID {mpxj_resource.getID()} has no StandardRate, using Cost field ({cost_val}). Assuming it's total cost or not per hour.")
                     # We can't assume it's per hour, return 0 or the value with warning.
                     # return float(str(cost_val)) # Could be incorrect
                     return 0.0 # More secure to return 0 if there's no hourly rate
        except Exception as e:
            print(f"Adv (MPXJReader): Error getting cost/h for Resource ID {mpxj_resource.getID()}: {e}")
        return 0.0 # Default cost if cannot be obtained

    def load(self, file_path: str) -> Project:
        global _mpxj_reader_instance

        if not _jvm_started: raise RuntimeError("MPXJReader: JVM is not started.")
        if not os.path.exists(file_path): raise FileNotFoundError(f"MPXJReader: File not found: {file_path}")
        
        print(f"Info (MPXJReader): Loading from '{file_path}'...")
        project = Project()
        project._clear_project_data()
        task_map: Dict[int, Task] = {}
        # Map to relate MPXJ resource ID with Python Resource object
        resource_map: Dict[int, Resource] = {}

        try:
            reader = self.MPXJUniversalReader()
            mpxj_project: Optional['ProjectFile'] = reader.read(JString(file_path))

            if mpxj_project is None: raise ValueError("MPXJ returned a null project.")

            project.project_name = str(mpxj_project.getProjectHeader().getProjectTitle()) or os.path.basename(file_path)

            # --- Process Resources First ---
            mpxj_resources = mpxj_project.getResources()
            if mpxj_resources:
                print(f"Info (MPXJReader): Processing {mpxj_resources.size()} MPXJ resources...")
                for mpxj_res in mpxj_resources:
                    try:
                        res_id = int(mpxj_res.getID()) # Use getID() which is usually more stable than UniqueID for resources
                        res_unique_id = int(mpxj_res.getUniqueID()) # Also save UniqueID just in case
                        res_name = str(mpxj_res.getName()) or f"Unnamed Resource {res_id}"

                        # Get cost per hour
                        cost_per_hour = self._get_cost_per_hour(mpxj_res)

                        # Create Python Resource object
                        py_resource = Resource(resource_id=res_id, name=res_name, cost_per_hour=cost_per_hour)
                        project.add_resource(py_resource)
                        resource_map[res_unique_id] = py_resource # Map by UniqueID for assignments
                        print(f"  -> Resource Created: {py_resource}")

                    except Exception as res_e:
                        print(f"Adv (MPXJReader): Error processing MPXJ resource: {res_e}")
                print(f"Info (MPXJReader): {len(project.resources)} Python resources created and added to project.")
            else:
                print("Adv (MPXJReader): No resources found in MPXJ file.")
                # Consider whether to throw an error here if resources are mandatory
                # raise ValueError("No resources found in MPXJ file, required for simulation.")

            # --- Process Tasks ---
            mpxj_tasks = mpxj_project.getTasks()
            if mpxj_tasks:
                print(f"Info (MPXJReader): Processing {mpxj_tasks.size()} MPXJ tasks...")
                for mpxj_task in mpxj_tasks:
                    is_summary = bool(mpxj_task.getSummary())
                    # Use UniqueID for tasks, it's the consistent key
                    task_unique_id = int(mpxj_task.getUniqueID())

                    # Ignore root task (ID=0) and summary tasks
                    if task_unique_id == 0 or is_summary: continue

                    try:
                        task_name = str(mpxj_task.getName()) or f"Unnamed Task {task_unique_id}"
                        mpxj_duration_obj = mpxj_task.getDuration()
                        duration_hours = 0.0
                        if mpxj_duration_obj:
                             try:
                                 # Get duration in minutes and convert to hours
                                 duration_minutes = mpxj_duration_obj.getDuration() # Numeric value
                                 duration_units = mpxj_duration_obj.getUnits() # TimeUnit (MINUTES, HOURS, etc.)
                                 if duration_minutes is not None:
                                     # Convert to hours based on the unit
                                     if duration_units == self.MPXJTimeUnit.MINUTES:
                                         duration_hours = float(duration_minutes) / 60.0
                                     elif duration_units == self.MPXJTimeUnit.HOURS:
                                         duration_hours = float(duration_minutes)
                                     elif duration_units == self.MPXJTimeUnit.DAYS:
                                         duration_hours = float(duration_minutes) * 8.0 # Assume 8h/day
                                     elif duration_units == self.MPXJTimeUnit.WEEKS:
                                          duration_hours = float(duration_minutes) * 40.0 # Assume 40h/week
                                     else:
                                         print(f"Adv (MPXJReader): Duration unit not handled '{duration_units}' for Task ID {task_unique_id}. Using value as is.")
                                         duration_hours = float(duration_minutes) # Could be incorrect
                             except Exception as dur_e:
                                 print(f"Adv (MPXJReader): Error converting duration for Task ID {task_unique_id}: {dur_e}")

                        task_cost = 0.0
                        try:
                            cost_obj = mpxj_task.getCost() # Estimated cost of the task (BCWS)
                            if cost_obj is not None:
                                task_cost = float(str(cost_obj)) # Convert currency to float
                        except Exception as cost_e:
                            print(f"Adv (MPXJReader): Error getting cost for Task ID {task_unique_id}: {cost_e}")

                        # Create Python Task object
                        py_task = Task(task_id=task_unique_id, name=task_name,
                                       duration=duration_hours, estimated_cost=task_cost)

                        # --- Process Resource Assignments for this task ---
                        assignments = mpxj_task.getResourceAssignments()
                        assigned_resource_id: Optional[int] = None
                        if assignments and not assignments.isEmpty():
                            if assignments.size() > 1:
                                print(f"Adv (MPXJReader): Task ID {task_unique_id} ('{task_name}') has {assignments.size()} assignments. Using the first one.")
                            # Take the first assignment (simplification)
                            first_assignment: Optional['ResourceAssignment'] = assignments.get(0)
                            if first_assignment:
                                assigned_mpxj_res_unique_id = int(first_assignment.getResourceUniqueID())
                                # Search the corresponding Python resource in our map
                                assigned_py_resource = resource_map.get(assigned_mpxj_res_unique_id)
                                if assigned_py_resource:
                                    assigned_resource_id = assigned_py_resource.id # Save the ID of the Python resource
                                else:
                                    print(f"Adv (MPXJReader): Assigned resource (UniqueID={assigned_mpxj_res_unique_id}) to Task ID {task_unique_id} not found in processed resources.")

                        # Set the required resource in the Python task
                        py_task.required_resource_id = assigned_resource_id
                        # --- END Process Assignments ---

                        task_map[task_unique_id] = py_task
                        project.add_task(py_task)

                    except Exception as create_e:
                        print(f"Adv (MPXJReader): Error creating Python Task UID={task_unique_id}: {create_e}")
                        # traceback.print_exc() # Descomentar para depuración detallada

                print(f"Info (MPXJReader): {len(project.tasks)} work tasks created and added to project.")
            else:
                print("Adv (MPXJReader): No tasks found in MPXJ file.")
                raise ValueError("No valid tasks found in MPXJ file.")


            # --- Process Dependencies ---
            added_deps = 0
            if mpxj_tasks:
                for mpxj_task in mpxj_tasks:
                    target_py_task = task_map.get(int(mpxj_task.getUniqueID()))
                    if target_py_task:
                        predecessors = mpxj_task.getPredecessors()
                        if predecessors and not predecessors.isEmpty():
                            for relation in predecessors:
                                # Consider only Start-to-Finish (FS) dependencies for now
                                if str(relation.getType()) == "FS":
                                    source_mpxj_task = relation.getTargetTask()
                                    if source_mpxj_task:
                                        source_unique_id = int(source_mpxj_task.getUniqueID())
                                        source_py_task = task_map.get(source_unique_id)
                                        if source_py_task:
                                            # Add dependency if it doesn't exist yet
                                            if source_py_task not in target_py_task.dependencies:
                                                target_py_task.dependencies.append(source_py_task)
                                                added_deps += 1
                                        # else: # Debug: Predecessor task not found in map
                                        #     print(f"Adv (MPXJReader): Tarea predecesora (UID={source_unique_id}) para Tarea ID {target_py_task.id} no encontrada en task_map.")
                print(f"Info (MPXJReader): {added_deps} FS dependencies added.")

            # Calculate baseline metrics (total estimated cost of tasks)
            project._calculate_baseline_metrics()
            print(f"Info (MPXJReader): Load completed. Project '{project.project_name}'.")
            print(f"  Tasks: {len(project.tasks)}, Resources: {len(project.resources)}, Planned Base Cost: {project.baseline_cost:.2f}")

        except jpype.JException as jex: # Capture specific Java/JPype exceptions
             print(f"Error Critical (MPXJReader - Java): Failed to process file: {jex}")
             print("Java stack trace:")
             print(jex.stacktrace())
             raise ValueError(f"MPXJReader: Failed to process '{file_path}' due to Java error: {jex.getMessage()}")
        except Exception as e:
            print(f"Error Critical (MPXJReader - Python): Failed to process file: {e}")
            traceback.print_exc()
            raise ValueError(f"MPXJReader: Failed to read or process '{file_path}': {e}")

        # Validate that the project has resources if they are required
        if not project.resources:
             print("Error Critical (MPXJReader): No resources loaded from MPXJ file. Simulation requires resources.")
             raise ValueError("Loaded project does not contain resources.")

        return project