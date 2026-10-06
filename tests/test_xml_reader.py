"""
Tests for XmlProjectReader: dependencies, work, resource UID/ID mapping,
multi-resource tasks and error reporting.
"""

import os

import pytest

from core.exceptions import ReaderError
from core.project import Project
from core.readers.xml_reader import XmlProjectReader

SAMPLE_XML = os.path.join(os.path.dirname(__file__), "..", "data", "Software Development Plan.xml")


def write_project(tmp_path, resources="", tasks="", assignments=""):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
  <Name>Test</Name>
  <Resources>{resources}</Resources>
  <Tasks>{tasks}</Tasks>
  <Assignments>{assignments}</Assignments>
</Project>"""
    path = tmp_path / "project.xml"
    path.write_text(xml, encoding="utf-8")
    return str(path)


def resource(uid, rid, name, rate):
    return f"<Resource><UID>{uid}</UID><ID>{rid}</ID><Type>1</Type><Name>{name}</Name><StandardRate>{rate}</StandardRate></Resource>"


def task(uid, duration="PT8H0M0S", work="PT8H0M0S", cost="0", preds=(), link_type=1, summary=0):
    links = "".join(f"<PredecessorLink><PredecessorUID>{p}</PredecessorUID><Type>{link_type}</Type></PredecessorLink>"
                    for p in preds)
    work_elem = f"<Work>{work}</Work>" if work is not None else ""
    return (f"<Task><UID>{uid}</UID><ID>{uid}</ID><Name>T{uid}</Name><Summary>{summary}</Summary>"
            f"<Duration>{duration}</Duration>{work_elem}<Cost>{cost}</Cost>{links}</Task>")


def assignment(task_uid, res_uid, work="PT8H0M0S"):
    return f"<Assignment><TaskUID>{task_uid}</TaskUID><ResourceUID>{res_uid}</ResourceUID><Work>{work}</Work></Assignment>"


def load_project(path):
    return Project(XmlProjectReader().load(path))


# --- Sample plan ---

def test_sample_plan_loads_all_dependencies():
    project = load_project(SAMPLE_XML)

    assert len(project.tasks) == 74
    assert sum(len(t.dependencies) for t in project.tasks.values()) == 84
    assert [d.id for d in project.tasks[3].dependencies] == [2]


def test_sample_plan_uses_work_for_effort_and_matches_planned_cost():
    project = load_project(SAMPLE_XML)

    task3 = project.tasks[3]
    assert task3.duration == 8.0
    assert task3.work == 1.0
    # Plan cost is work x rate: 1h of Management at 33/h
    assert task3.estimated_cost == pytest.approx(task3.work * project.resources[1].cost_per_hour)


# --- Dependencies ---

def test_dependencies_are_read_from_links_inside_the_successor(tmp_path):
    path = write_project(tmp_path, tasks=task(1) + task(2, preds=[1]) + task(3, preds=[1, 2]))

    project = load_project(path)

    assert [d.id for d in project.tasks[2].dependencies] == [1]
    assert sorted(d.id for d in project.tasks[3].dependencies) == [1, 2]
    assert project.tasks[1].dependencies == []


def test_non_finish_to_start_and_summary_links_are_ignored(tmp_path):
    path = write_project(tmp_path, tasks=(
        task(1, summary=1) + task(2) + task(3, preds=[1]) + task(4, preds=[2], link_type=3)))

    project = load_project(path)

    assert project.tasks[3].dependencies == []  # predecessor is a summary task
    assert project.tasks[4].dependencies == []  # start-to-start link


# --- Work ---

def test_work_falls_back_to_duration_when_missing(tmp_path):
    path = write_project(tmp_path, tasks=task(1, duration="PT6H0M0S", work=None) +
                                         task(2, duration="PT6H0M0S", work="PT0H0M0S"))

    project = load_project(path)

    assert project.tasks[1].work == 6.0
    assert project.tasks[2].work == 0.0  # explicit zero work is kept


# --- Resources and assignments ---

def test_assignments_map_resource_uid_to_resource_id(tmp_path):
    # UID 10 is the resource whose ID is 1; UID 20 has ID 2.
    path = write_project(
        tmp_path,
        resources=resource(10, 1, "Alice", 30) + resource(20, 2, "Bob", 40),
        tasks=task(1) + task(2),
        assignments=assignment(1, 20) + assignment(2, 10),
    )

    project = load_project(path)

    assert set(project.resources) == {1, 2}
    assert project.tasks[1].required_resource_id == 2  # Bob
    assert project.tasks[2].required_resource_id == 1  # Alice


def test_multi_resource_task_keeps_resource_with_most_work(tmp_path):
    path = write_project(
        tmp_path,
        resources=resource(1, 1, "Alice", 30) + resource(2, 2, "Bob", 40),
        tasks=task(1),
        assignments=assignment(1, 1, "PT2H0M0S") + assignment(1, 2, "PT6H0M0S"),
    )

    project = load_project(path)

    assert project.tasks[1].required_resource_id == 2
    assert project.tasks[1].get_metadata("assigned_resource_ids") == [1, 2]


# --- Errors are raised, not swallowed ---

def test_invalid_duration_raises_reader_error_naming_the_task(tmp_path):
    path = write_project(tmp_path, tasks=task(7, duration="eight hours"))

    with pytest.raises(ReaderError, match="task 7"):
        XmlProjectReader().load(path)


def test_invalid_cost_raises_reader_error(tmp_path):
    path = write_project(tmp_path, tasks=task(1, cost="lots"))

    with pytest.raises(ReaderError, match="cost"):
        XmlProjectReader().load(path)


def test_malformed_xml_raises_reader_error(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text("<Project><Tasks>", encoding="utf-8")

    with pytest.raises(ReaderError, match="Malformed XML"):
        XmlProjectReader().load(str(path))


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        XmlProjectReader().load(str(tmp_path / "nope.xml"))
