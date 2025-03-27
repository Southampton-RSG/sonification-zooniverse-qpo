import os
from panoptes_client import Panoptes, Subject, SubjectSet
from dotenv import load_dotenv
load_dotenv()


CLIENT_ID = '7fecf1c5d5a2e1d7c9a6ccf0344e5ae9f1fb6ad7b412192d31182c6cdb3da8ed'
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
PROJECT_ID = 23238
SUBJECT_SET_ID = 118526

EXAMPLES = [
    # subject, transits
    94880862,  # 3
    94880864,  # 3
    94879057,  # 3
    94878694,  # 2
    94879597,  # 2
    94879726,  # 2
    94880124,  # 2
    94879979,  # 2
    94878602,  # 1
    94878691,  # 2
    94880222,  # 3
    94879225,  # 3
    94880438,  # 3
    94879329,  # 3
    94878733,  # 2
    94878682,  # 2
    94878411,  # 2
    94878661,  # 2
    94880022,  # 1
    94880415,  # 1
]

originals = []
for subject_id in EXAMPLES:
    original = Subject.find(subject_id)
    originals.append(original)

with Panoptes(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    subject_set = SubjectSet.find(SUBJECT_SET_ID)
    subjects = []
    with Subject.async_saves():
        for original in originals:
            subject = Subject()
            subject.metadata.update(original.metadata)
            subject.metadata['!PH-TESS Subject'] = original.id
            subject.add_location(f'mp3/sims/{original.id}.mp3')
            subject.links.project = PROJECT_ID
            subject.save()
            subjects.append(subject)
    subject_set.add(subjects)
