import time
import obswebsocket
from obswebsocket import requests as obsrequests
from obswebsocket import events as obsevents
from config import OBS_WS_HOST, OBS_WS_PASSWORD, OBS_WS_PORT, OBS_TRANSITION_TIMEOUT

class OBSTextSwitcher:
    def __init__(self):
        self.client = obswebsocket.obsws(OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD, authreconnect=3)
        self.client.connect()
        self.client.register(self._input_name_changed, obsevents.InputNameChanged)
        self.client.register(self._scene_name_changed, obsevents.SceneNameChanged)
        self.client.register(self._transition_started, obsevents.SceneTransitionStarted)
        self.client.register(self._transition_ended, obsevents.SceneTransitionEnded)
        self.transition_start_time = None
        self.scene1 = None
        self.scene2 = None
        self.source1 = None
        self.source2 = None

    def disconnect(self):
        self.client.disconnect()
    
    def _input_name_changed(self, event):
        old_name = event.getOldInputName()
        new_name = event.getInputName()
        if old_name == self.source1:
            self.source1 = new_name
        if old_name == self.source2:
            self.source2 = new_name

    def _scene_name_changed(self, event):
        old_name = event.getOldSceneName()
        new_name = event.getSceneName()
        if old_name == self.scene1:
            self.scene1 = new_name
        if old_name == self.scene1:
            self.scene1 = new_name

    def _transition_started(self, _):
        self.transition_start_time = time.time()
    
    def _transition_ended(self, _):
        self.transition_start_time = None
    
    def is_transition_active(self):
        if self.transition_start_time is None:
            return False
        if time.time() > self.transition_start_time + OBS_TRANSITION_TIMEOUT:
            self.transition_start_time = None
            return False
        return True
    
    def save_settings(self):
        settings = dict(scene1=self.scene1, scene2=self.scene2,
                        source1=self.source1, source2=self.source2)
        self.client.call(obsrequests.SetPersistentData(realm="OBS_WEBSOCKET_DATA_REALM_GLOBAL",
                                                        slotName=f"osc_text_switcher_settings",
                                                        slotValue=settings))

    def load_settings(self):
        request = obsrequests.GetPersistentData(realm="OBS_WEBSOCKET_DATA_REALM_GLOBAL",
                                                slotName=f"osc_text_switcher_settings")
        settings = self.client.call(request).getSlotValue()
        if not isinstance(settings, dict):
            return
        self.scene1 = settings.get("scene1", None)
        self.scene2 = settings.get("scene2", None)
        self.source1 = settings.get("source1", None)
        self.source2 = settings.get("source2", None)

    def is_studio_mode(self):
        return self.client.call(obsrequests.GetStudioModeEnabled()).getStudioModeEnabled()

    def set_input_text(self, input_name, text):
        self.client.call(obsrequests.SetInputSettings(inputName=input_name, inputSettings={"text": text}))

    def get_scene_names(self):
        scenes = self.client.call(obsrequests.GetSceneList()).getScenes()
        return [scene["sceneName"] for scene in reversed(scenes)]

    def get_text_sources(self, scene_name):
        scene_item_list = self.client.call(obsrequests.GetSceneItemList(sceneName=scene_name)).getSceneItems()
        return list(reversed([item["sourceName"] for item in scene_item_list if item["inputKind"] in ["text_gdiplus_v2", "text_gdiplus_v3"]]))

    def get_program_scene(self):
        return self.client.call(obsrequests.GetCurrentProgramScene()).getCurrentProgramSceneName()

    def switch_to_scene(self, scene_name):
        # if self.is_studio_mode():
            # self.client.call(obsrequests.SetCurrentPreviewScene(sceneName=scene_name))
            # self.client.call(obsrequests.TriggerStudioModeTransition())
        # else:
        self.client.call(obsrequests.SetCurrentProgramScene(sceneName=scene_name))

    def switch_text(self, new_text):
        scene2_active = self.get_program_scene() == self.scene2
        if self.scene1 is None or self.scene2 is None:
            return False
        if self.source1 is None or self.source2 is None:
            return False
        if self.is_transition_active():
            return False
        
        self.set_input_text(self.source1 if scene2_active else self.source2, new_text)
        self.switch_to_scene(self.scene1 if scene2_active else self.scene2)
        return True

if __name__ == "__main__":
    switcher = OBSTextSwitcher()
