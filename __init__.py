from mycroft import MycroftSkill, intent_file_handler


class SkyQ(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('q.sky.intent')
    def handle_q_sky(self, message):
        self.speak_dialog('q.sky')


def create_skill():
    return SkyQ()

