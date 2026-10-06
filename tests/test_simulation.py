"""
Regression tests for task execution, agent release, planned value (PV/SPI),
the parallel assignment strategy and work-based effort.

All tests use error_margin=0 so progress is deterministic. Random morale events
only fire when teams exist; team tests assert on assignment, not on timing.
"""

import pytest

from core.entities import Task, Resource, TaskStatus
from core.simulation.model import ProjectManagementModel
from core.simulation.parameters import SimulationParameters


def make_task(task_id, duration, cost=0.0, required=None, deps=(), work=None):
    task = Task(task_id=task_id, name=f"T{task_id}", duration=duration, estimated_cost=cost, work=work)
    task.required_resource_id = required
    for dep in deps:
        task.add_dependency(dep)
    return task


def make_resources(*ids, cost_per_hour=10.0):
    return [Resource(resource_id=i, name=f"R{i}", cost_per_hour=cost_per_hour) for i in ids]


def make_model(tasks, resources, strategy="greedy", teams=None):
    params = SimulationParameters(error_margin=0.0, max_steps=500,
                                  team_definitions=teams or [], assignment_strategy=strategy)
    return ProjectManagementModel(tasks=tasks, resources=resources, params=params)


# --- Problem 1: individual tasks must take their duration, not finish instantly ---

@pytest.mark.parametrize("strategy", ["greedy", "shortest_first", "parallel"])
def test_individual_task_takes_its_full_duration(strategy):
    task = make_task(1, duration=4, cost=40, required=1)
    model = make_model([task], make_resources(1), strategy)

    for _ in range(3):
        model.step()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.progress == pytest.approx(0.75)

    model.step()
    assert task.status == TaskStatus.DONE
    assert task.real_duration == 4
    assert model.agents_by_resource_id[1].worked_hours == 4


# --- Problem 2: agents are released after finishing, so they can take the next task ---

@pytest.mark.parametrize("strategy", ["greedy", "shortest_first", "parallel"])
def test_agent_is_released_and_picks_up_next_task(strategy):
    first = make_task(1, duration=4, required=1)
    second = make_task(2, duration=4, required=1, deps=[first])
    model = make_model([first, second], make_resources(1), strategy)

    model.run_model()

    assert first.status == TaskStatus.DONE
    assert second.status == TaskStatus.DONE
    assert not model.running
    assert model.agents_by_resource_id[1].is_available()
    assert model.agents_by_resource_id[1].worked_hours == 8


def test_individual_assignment_records_resource_on_task():
    task = make_task(1, duration=4, required=1)
    model = make_model([task], make_resources(1))

    model.step()

    assert task.assigned_resource is not None
    assert task.assigned_resource.id == 1


@pytest.mark.parametrize("strategy", ["greedy", "shortest_first", "parallel"])
def test_task_without_required_resource_is_worked_by_an_idle_agent(strategy):
    task = make_task(1, duration=4, required=None)
    model = make_model([task], make_resources(1), strategy)

    model.run_model()

    assert task.status == TaskStatus.DONE
    assert task.real_duration == 4


def test_milestone_completes_once_dependencies_are_met_and_does_not_block():
    work = make_task(1, duration=4, required=1)
    milestone = make_task(2, duration=0, deps=[work])
    after = make_task(3, duration=4, required=1, deps=[milestone])
    model = make_model([work, milestone, after], make_resources(1))

    model.run_model()

    assert all(t.status == TaskStatus.DONE for t in (work, milestone, after))
    assert model.steps == 8


# --- Problem 3: PV/SPI follow the planned schedule over time ---

def test_planned_schedule_is_early_start_from_dependencies():
    a = make_task(1, duration=4, cost=40, required=1)
    b = make_task(2, duration=6, cost=60, required=1, deps=[a])
    c = make_task(3, duration=10, cost=100, required=2)
    model = make_model([a, b, c], make_resources(1, 2))

    assert model.planned_start == {1: 0.0, 2: 4.0, 3: 0.0}


@pytest.mark.parametrize("time, expected_pv", [
    (0, 0.0),
    (2, 40 * 0.5 + 100 * 0.2),           # A half done, C 20%
    (7, 40 + 60 * 0.5 + 100 * 0.7),      # A done, B half, C 70%
    (20, 200.0),                         # everything planned complete
])
def test_planned_value_depends_on_time(time, expected_pv):
    a = make_task(1, duration=4, cost=40, required=1)
    b = make_task(2, duration=6, cost=60, required=1, deps=[a])
    c = make_task(3, duration=10, cost=100, required=2)
    model = make_model([a, b, c], make_resources(1, 2))

    model.steps = time

    assert model.total_planned_value() == pytest.approx(expected_pv)


def test_spi_drops_below_one_when_a_shared_resource_delays_work():
    # Both tasks are planned in parallel, but one resource must do them in sequence.
    a = make_task(1, duration=4, cost=40, required=1)
    c = make_task(2, duration=4, cost=40, required=1)
    model = make_model([a, c], make_resources(1))

    for _ in range(4):
        model.step()

    # PV = 80 (both planned done), EV = 40 (only one done)
    assert model.total_planned_value() == pytest.approx(80)
    assert model.total_earned_value() == pytest.approx(40)
    assert model.schedule_performance_index() == pytest.approx(0.5)


def test_dependency_cycle_is_rejected():
    a = make_task(1, duration=4, required=1)
    b = make_task(2, duration=4, required=1, deps=[a])
    a.add_dependency(b)

    with pytest.raises(ValueError, match="cycle"):
        make_model([a, b], make_resources(1))


# --- Problem 4: parallel strategy matches tasks to the teams that own the resource ---

def test_parallel_assigns_each_team_the_task_matching_its_members():
    needs_r2 = make_task(1, duration=4, required=2)
    needs_r1 = make_task(2, duration=4, required=1)
    teams = [
        {"id": 1, "name": "Team R1", "member_resource_ids": [1]},
        {"id": 2, "name": "Team R2", "member_resource_ids": [2]},
    ]
    model = make_model([needs_r2, needs_r1], make_resources(1, 2), "parallel", teams)

    model.assignment_strategy.assign_tasks()

    assert needs_r1.assigned_team.id == 1
    assert needs_r2.assigned_team.id == 2


def test_parallel_prefers_owning_agent_over_cross_training_team():
    needs_r2 = make_task(1, duration=4, required=2)
    teams = [{"id": 1, "name": "Team R1", "member_resource_ids": [1]}]
    model = make_model([needs_r2], make_resources(1, 2), "parallel", teams)

    model.assignment_strategy.assign_tasks()

    assert needs_r2.assigned_team is None
    assert needs_r2.assigned_resource.id == 2


def test_parallel_cross_trains_when_no_owner_is_available():
    needs_r2 = make_task(1, duration=4, required=2)
    blocker = make_task(2, duration=10, required=2)
    teams = [{"id": 1, "name": "Team R1", "member_resource_ids": [1]}]
    # Agent 2 is busy with `blocker`, so the idle team takes the other task with a penalty.
    model = make_model([blocker, needs_r2], make_resources(1, 2), "parallel", teams)

    model.assignment_strategy.assign_tasks()

    assert blocker.assigned_resource.id == 2
    assert needs_r2.assigned_team.id == 1


# --- Effort is driven by Work, not Duration ---

def test_task_effort_comes_from_work_not_duration():
    task = make_task(1, duration=8, work=2, cost=20, required=1)
    model = make_model([task], make_resources(1, cost_per_hour=10))

    model.run_model()

    assert model.steps == 2
    assert model.agents_by_resource_id[1].worked_hours == 2


def test_cpi_is_one_when_work_goes_exactly_to_plan():
    a = make_task(1, duration=8, work=2, cost=20, required=1)
    b = make_task(2, duration=8, work=3, cost=30, required=1, deps=[a])
    model = make_model([a, b], make_resources(1, cost_per_hour=10))

    model.run_model()

    assert model.total_actual_cost() == pytest.approx(50)
    assert model.cost_performance_index() == pytest.approx(1.0)


def test_only_the_used_fraction_of_the_final_step_is_charged():
    task = make_task(1, duration=8, work=1.5, cost=15, required=1)
    model = make_model([task], make_resources(1, cost_per_hour=10))

    model.run_model()

    assert model.steps == 2
    assert model.agents_by_resource_id[1].worked_hours == pytest.approx(1.5)
    assert model.total_actual_cost() == pytest.approx(15)


def test_zero_work_task_completes_without_effort():
    setup = make_task(1, duration=8, work=0)  # e.g. lead time with no assigned effort
    after = make_task(2, duration=4, required=1, deps=[setup])
    model = make_model([setup, after], make_resources(1))

    model.run_model()

    assert setup.status == TaskStatus.DONE
    assert model.steps == 4


def test_planned_schedule_and_completion_use_work():
    a = make_task(1, duration=8, work=2, cost=20, required=1)
    b = make_task(2, duration=8, work=6, cost=60, required=1, deps=[a])
    model = make_model([a, b], make_resources(1))

    assert model.planned_start == {1: 0.0, 2: 2.0}

    model.step()
    model.step()
    assert model.project_completion_percentage() == pytest.approx(25.0)  # 2 of 8 work hours


def test_sample_plan_runs_in_dependency_order_with_cpi_near_one():
    import io
    import contextlib
    from core.project import Project
    from core.readers.xml_reader import XmlProjectReader
    from tests.test_xml_reader import SAMPLE_XML

    with contextlib.redirect_stdout(io.StringIO()):
        project = Project(XmlProjectReader().load(SAMPLE_XML))
    model = make_model(project.get_tasks_for_simulation(), project.get_resources_for_simulation())

    while model.running and model.steps < 500:
        model.step()
        for task in model.task_map.values():
            if task.status != TaskStatus.TO_DO:
                assert all(dep.status == TaskStatus.DONE for dep in task.dependencies), task.id

    assert all(t.status == TaskStatus.DONE for t in model.task_map.values())
    assert model.cost_performance_index() == pytest.approx(1.0)
