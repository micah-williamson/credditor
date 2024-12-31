from __future__ import annotations

import dataclasses
import datetime
import json
import os
from typing import Dict

from dacite import from_dict, Config

from models.load_user_settings import LoadUserSettings
from models.user_data import UserData


class SaveState:
    load_user_settings: LoadUserSettings
    user_data: Dict[str, UserData]

    @classmethod
    def __cls_init__(cls):
        # Defaults
        cls.load_user_settings = LoadUserSettings(
            username=''
        )
        cls.user_data = dict()

        # If any saved state exists attempt to overwrite the defaults
        if not os.path.exists('data/save_state.dat'):
            return

        with open('data/save_state.dat', 'r') as file:
            json_str = file.read()
            dacite_config = Config(type_hooks={
                datetime.date: lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
                datetime.datetime: lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
            })
            if json_str:
                json_dict = json.loads(json_str)
                SaveState.load_user_settings = from_dict(data_class=LoadUserSettings,
                                                         data=json_dict['load_user_settings'],
                                                         config=dacite_config)
                for key, value in json_dict.get('user_data', {}).items():
                    SaveState.user_data[key] = from_dict(data_class=UserData, data=value,
                                                         config=dacite_config)

    @classmethod
    def save(cls):
        if not os.path.exists('data'):
            os.makedirs('data')
        with open('data/save_state.dat', 'w+') as file:
            file.write(json.dumps({
                'load_user_settings': dataclasses.asdict(cls.load_user_settings),
                'user_data': {key: dataclasses.asdict(value) for key, value in
                              cls.user_data.items()}
            }, default=str))
