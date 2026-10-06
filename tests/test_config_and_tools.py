"""
Tests for reproducibility (seeds), configuration validation, the reader factory
and the cleanup script.
"""

import pytest

import core.interfaces
import core.project
from core.entities import Resource
from core.readers import create_reader, get_reader_types, validate_reader
from core.readers.xml_reader import XmlProjectReader
from core.simulation.model import ProjectManagementModel
from core.simulation.parameters import SimulationParameters
from core.simulation.runner import ExperimentConfig, SimulationRunner
from tests.test_simulation import make_resources, make_task
from tests.test_xml_reader import SAMPLE_XML, task, write_project

TEAMS = [{"id": 1, "name": "A", "member_resource_ids": [1, 2]},
         {"id": 2, "name": "B", "member_resource_ids": [3]}]


def run_sample_model(seed):
    project = core.project.Project(XmlProjectReader().load(SAMPLE_XML))
    params = SimulationParameters(error_margin=0.15, max_steps=500, team_definitions=TEAMS,
                                  assignment_strategy="parallel", seed=seed)
    model = ProjectManagementModel(project.get_tasks_for_simulation(),
                                   project.get_resources_for_simulation(), params)
    model.run_model()
    return model.datacollector.get_model_vars_dataframe()


# --- Reproducibility ---

def test_same_seed_reproduces_a_run_exactly():
    assert run_sample_model(seed=42).equals(run_sample_model(seed=42))


def test_different_seeds_give_different_runs():
    assert not run_sample_model(seed=1).equals(run_sample_model(seed=2))


def test_runner_seed_makes_whole_experiment_reproducible(tmp_path):
    def run():
        cfg = ExperimentConfig()
        cfg.mpp_file_name = "Software Development Plan.xml"
        cfg.num_simulations = 2
        cfg.team_definitions = TEAMS
        cfg.output_folder_relative_path = str(tmp_path)
        cfg.print_last_run_summary = False
        cfg.seed = 7
        runner = SimulationRunner(cfg)
        runner.run()
        return runner.aggregated_results

    first, second = run(), run()
    assert first.equals(second)
    # Each simulation in the experiment gets its own seed, so runs differ from each other
    runs = [df.drop(columns="simulation_id").reset_index(drop=True) for _, df in first.groupby("simulation_id")]
    assert not runs[0].equals(runs[1])


# --- Configuration validation ---

def test_unknown_team_member_is_rejected():
    teams = [{"id": 1, "name": "Ghosts", "member_resource_ids": [1, 99]}]
    params = SimulationParameters(team_definitions=teams)

    with pytest.raises(ValueError, match=r"unknown resource IDs \[99\]"):
        ProjectManagementModel([make_task(1, 4, required=1)], make_resources(1), params)


def test_resource_in_two_teams_is_rejected():
    teams = [{"id": 1, "name": "A", "member_resource_ids": [1]},
             {"id": 2, "name": "B", "member_resource_ids": [1, 2]}]
    params = SimulationParameters(team_definitions=teams)

    with pytest.raises(ValueError, match="already belong to another team"):
        ProjectManagementModel([make_task(1, 4, required=1)], make_resources(1, 2), params)


def test_resource_efficiency_is_used_by_its_agent():
    fast = Resource(resource_id=1, name="Fast", cost_per_hour=10.0, efficiency=2.0)
    params = SimulationParameters(error_margin=0.0)
    model = ProjectManagementModel([make_task(1, duration=8, work=4, required=1)], [fast], params)

    model.run_model()

    assert model.steps == 2


def test_reassignment_frequency_warns_that_it_has_no_effect(capsys):
    params = SimulationParameters(reassignment_frequency=5)
    ProjectManagementModel([make_task(1, 4, required=1)], make_resources(1), params)

    assert "reassignment_frequency=5 is not implemented" in capsys.readouterr().out


def test_runner_rejects_the_unrelated_core_config_experiment_config():
    from core.config import ExperimentConfig as CoreExperimentConfig

    with pytest.raises(TypeError, match="core.simulation.runner.ExperimentConfig"):
        SimulationRunner(CoreExperimentConfig())


# --- Reader factory ---

def test_xml_reader_is_registered_in_the_factory():
    assert "xml" in get_reader_types()
    assert isinstance(create_reader(SAMPLE_XML), XmlProjectReader)
    assert validate_reader("xml") == []


def test_project_data_has_a_single_definition():
    assert core.interfaces.ProjectData is core.project.ProjectData


def test_reader_validates_loaded_data():
    reader = XmlProjectReader()
    assert reader.validate_data(reader.load(SAMPLE_XML))


def test_link_lags_are_reported(tmp_path, capsys):
    lagged = task(2).replace("</Task>", "<PredecessorLink><PredecessorUID>1</PredecessorUID><Type>1</Type>"
                                        "<LinkLag>-4800</LinkLag></PredecessorLink></Task>")
    path = write_project(tmp_path, tasks=task(1) + lagged)

    XmlProjectReader().load(path)

    assert "1 link(s) have a lag or lead" in capsys.readouterr().out


# --- Cleanup script ---

def test_cleanup_only_touches_generated_files_under_the_project(tmp_path):
    from cleanup_generated import cleanup_generated_files

    generated = tmp_path / "core" / "generated"
    generated.mkdir(parents=True)
    (generated / "run.csv").write_text("x")
    (generated / ".gitkeep").write_text("")
    pkg_cache = tmp_path / "core" / "__pycache__"
    pkg_cache.mkdir()
    venv_cache = tmp_path / ".venv" / "lib" / "__pycache__"
    venv_cache.mkdir(parents=True)
    data = tmp_path / "data" / "plan.xml"
    data.parent.mkdir()
    data.write_text("<Project/>")

    cleanup_generated_files(root=tmp_path)

    assert not (generated / "run.csv").exists()
    assert not pkg_cache.exists()
    assert (generated / ".gitkeep").exists()
    assert venv_cache.exists()
    assert data.exists()
