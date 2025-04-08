"""
Uploads all (not previously uploaded) files in the Zooniverse data folder
"""
from typing import Dict, Any, List
import yaml
import logging
from pathlib import Path
from logging import getLogger, StreamHandler, FileHandler, Formatter, Logger
from panoptes_client import Panoptes, Project, SubjectSet, Subject, Workflow
from configparser import ConfigParser


def main():
    config: ConfigParser = ConfigParser()
    config.read(
        [
            'settings.default.ini', 'settings.ini'
        ]
    )

    logger: Logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler: FileHandler = FileHandler(Path(config['PATHS']['logs']) / 'workflows_upload.log')
    stream_handler: StreamHandler = StreamHandler()

    log_formatter: Formatter = Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    file_handler.setFormatter(log_formatter)
    stream_handler.setFormatter(log_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Connect to Panoptes, and retrieve our project
    logger.debug(
        f"Connecting to Panoptes account '{config['ZOONIVERSE'].get('username')}'"
    )
    Panoptes.connect(
        username=config['ZOONIVERSE'].get('username'),
        password=config['ZOONIVERSE'].get('password'),
    )

    project: Project = Project(
        config['ZOONIVERSE'].getint('project_id'),
    )

    zooniverse_path: Path = Path(config['PATHS']['zooniverse'])
    subjects_path: Path = zooniverse_path / 'subjects'
    workflows_path: Path = zooniverse_path / 'workflows'
    workflow_template: Workflow = Workflow.find(config['ZOONIVERSE'].getint('template_workflow'))

    if not workflow_template:
        logger.error(f"Template workflow ID {config['ZOONIVERSE'].getint('template_workflow')} not found")
    else:
        workflow_template_tasks: Dict[str, Any] = workflow_template.tasks

    work_done: Dict = {
        'workflows_created': 0,
    }
    for workflow_path in workflows_path.iterdir():
        if workflow_path.is_file():
            with workflow_path.open('r') as workflow_file:
                workflow_data: Dict = yaml.safe_load(workflow_file)

            logger.debug(
                f"{workflow_path}: Workflow ID {workflow_data['id']}"
            )

            if workflow_data.get('id', None):
                # If there is an ID present, let's try and find the workflow set
                workflow: Workflow = Workflow.find(workflow_data['id'])
                if not workflow:
                    # There is a recorded workflow ID, but we can't look it up on the Zooniverse
                    logger.error(
                        f"Workflow ID {workflow_data['id']} not found"
                    )
                else:
                    # There is a recorded subject set ID, and we can find it
                    logger.debug(
                        f"{workflow_path}: Workflow found, Zooniverse ID: {workflow_data['id']}"
                    )

            workflow.tasks = workflow_template_tasks
            workflow.save()

            subject_sets: List[SubjectSet] = []
            for subject_set_name in workflow_data['subject_sets']:
                logger.debug(f"{subjects_path/subject_set_name/'meta.yaml'}: Finding ID for subject set.")
                with open(subjects_path/subject_set_name/'meta.yaml', 'r') as subject_set_file:
                    subject_set_meta: Dict[str, Any] = yaml.safe_load(subject_set_file)

                subject_set: SubjectSet = SubjectSet.find(subject_set_meta['id'])
                if subject_set:
                    subject_sets.append(subject_set)

            workflow.add_subject_sets(subject_sets)
            workflow.save()


    print("Finished uploading:")
    print(f"- {work_done['workflows_created']} workflows")

if __name__ == "__main__":
    main()
