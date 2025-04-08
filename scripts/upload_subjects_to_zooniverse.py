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

    file_handler: FileHandler = FileHandler(Path(config['PATHS']['logs']) / 'panoptes_upload.log')
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

    work_done: Dict = {
        'workflows_created': 0,
        'subject_sets_created': 0,
        'subjects_created': 0,
    }
    for subject_set_directory in subjects_path.iterdir():
        if subject_set_directory.is_dir():
            # Open the metadata for this subject set, saved inside the directory
            subject_set_meta_path: Path = subject_set_directory / 'meta.yaml'

            with subject_set_meta_path.open('r') as subject_set_meta_file:
                subject_set_meta: Dict = yaml.safe_load(subject_set_meta_file)

            logger.debug(
                f"{subject_set_directory}: Subject set, name: {subject_set_meta['display_name']}"
            )

            if subject_set_meta.get('id', None):
                # If there is an ID present, let's try and find the subject set
                subject_set = SubjectSet.find(subject_set_meta['id'])
                if not subject_set:
                    # There is a recorded subject set ID, but we can't look it up on the Zooniverse
                    # So clear the ID, and save that there's no ID
                    logger.warning(
                        f"{subject_set_directory}: Subject set missing online, Zooniverse ID: {subject_set_meta['id']}"
                    )
                    subject_set_meta['id'] = None

                    with subject_set_meta_path.open('w') as subject_set_meta_file:
                        yaml.dump(subject_set_meta, subject_set_meta_file)

                else:
                    # There is a recorded subject set ID, and we can find it
                    logger.debug(
                        f"{subject_set_directory}: Subject set found, Zooniverse ID: {subject_set_meta['id']}"
                    )


            if not subject_set_meta.get('id', None):
                # There is no recorded subject set ID, so we need to create a new subject set
                subject_set: SubjectSet = SubjectSet()
                subject_set.links.project = project
                subject_set.display_name = subject_set_meta['display_name']
                subject_set.save()
                subject_set.reload()
                subject_set_meta['id'] = subject_set.id

                with subject_set_meta_path.open('w') as subject_set_meta_file:
                    yaml.dump(subject_set_meta, subject_set_meta_file)

                logger.debug(
                    f"{subject_set_directory}: Subject set created, Zooniverse ID: {subject_set_meta['id']}"
                )
                work_done['subject_sets_created']+= 1

            new_subjects: List[Subject] = []
            for subject_file in subject_set_directory.glob('*.mp4'):
                # Open the metadata for this subject, saved next to it
                subject_meta_path: Path = subject_file.with_suffix('.meta.yaml')

                with subject_meta_path.open('r') as subject_meta_file:
                    subject_meta: Dict = yaml.safe_load(subject_meta_file)

                if subject_meta.get('id', None):
                    # If the subject has an ID, try to find it
                    subject = Subject.find(subject_meta['id'])
                    if not subject:
                        # If it can't be found, then it's been deleted, so clear the ID
                        logger.warning(
                            f"{subject_file}: Subject missing online, Zooniverse ID: {subject_meta['id']}"
                        )
                        subject_meta['id'] = None
                        with subject_meta_path.open('w') as subject_meta_file:
                            yaml.dump(subject_meta, subject_meta_file)

                    else:
                        # There is a recorded subject set ID, and we can find it
                        logger.debug(
                            f"{subject_file}: Subject found, Zooniverse ID: {subject_meta['id']}"
                        )

                if not subject_meta.get('id', None):
                    # If there's no existing subject (either we didn't expect one, or it was missing).
                    # Create a new one.
                    subject: Subject = Subject()
                    subject.links.project = project
                    subject.add_location(str(subject_file))
                    for key, value in subject_meta.items():
                        subject.metadata[key] = value

                    try:
                        # Catch exceptions during subject save and continue.
                        # Otherwise, an error in 1 file would prevent the whole batch being added to the subject set.
                        # Loose subjects are a problem we have to keep track of.
                        subject.save()
                        subject.reload()
                        subject_meta['id'] = subject.id

                        with subject_meta_path.open('w') as subject_meta_file:
                            yaml.dump(subject_meta, subject_meta_file)

                        new_subjects.append(subject)

                        logger.debug(
                            f"{subject_file}: Subject created, Zooniverse ID: {subject_set_meta['id']}"
                        )
                        work_done['subjects_created']+= 1

                    except Exception as e:
                        logger.warning(
                            f"{subject_file}: Subject creation failed. Panoptes exception:\n{e}"
                        )

            if new_subjects:
                subject_set.add(new_subjects)
                subject_set.save()

    print("Finished uploading:")
    print(f"- {work_done['subject_sets_created']} subject sets")
    print(f"- {work_done['subjects_created']} subjects")

if __name__ == "__main__":
    main()
