from datetime import datetime, timedelta
from typing import List, Optional, Set

from discord import Client, Guild, Member, Message, TextChannel, VoiceChannel, VoiceState

RAD_ID = 244237344922796032
ATTENDANCE_REPORT_CHANNEL_ID = 1093964726641373244
VOICE_TESTING_ID = 1093966732906995763
RADS_POD_ID = 870717435953696828
MOD_CHAT_ID = 877284250704027650
PATRON_STREAM_CHANNEL_ID = 962086609455550494


class AttendanceBot(Client):
    def __init__(self, intents):
        self.report_channel: Optional[TextChannel] = None
        self.alert_channel: Optional[TextChannel] = None
        self.event_channel: Optional[VoiceChannel] = None
        self.host: Optional[Member] = None
        self.attendees: Set[Member] = set()
        self.recording: bool = False
        self.guild: Optional[Guild] = None
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        self.report_channel = await self.fetch_channel(ATTENDANCE_REPORT_CHANNEL_ID)
        self.event_channel = await self.fetch_channel(PATRON_STREAM_CHANNEL_ID)
        self.alert_channel = await self.fetch_channel(MOD_CHAT_ID)
        self.guild = await self.fetch_guild(RADS_POD_ID)
        self.host = await self.guild.fetch_member(RAD_ID)

        await self.alert_channel.send(f'Hello, I am now running')

        if self.host in self.event_channel.members:
            await self.start_recording()

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if before == after:
            return
        if member == self.host:
            if after.channel == self.event_channel:
                await self.start_recording()
            elif before.channel == self.event_channel:
                await self.stop_recording()
            else:
                return
        else:
            if self.recording and after.channel == self.event_channel:
                self.attendees.add(member)

    async def stop_recording(self):
        self.recording = False
        if self.attendees:
            previous_attendees: list[str] = await self.get_previous_attendees()
            new_attendees: list[str] = [user.name for user in self.attendees]
            if previous_attendees:
                new_attendees: list[str] = [user for user in new_attendees if user not in previous_attendees]
            if new_attendees:
                await self.report_channel.send('; '.join(new_attendees))
            else:
                await self.report_channel.send('No one showed up :(')
        else:
            await self.report_channel.send('No one showed up :(')
        # logic to figure out past messages and stuff
        await self.alert_channel.send(f'<@{self.host.id}> No longer recording attendance in {self.event_channel.name}')

    async def get_previous_attendees(self):

        start_of_week: datetime = datetime.today() - timedelta(days=datetime.today().isoweekday() % 7)
        messages: List[Message] = [message async for message in self.report_channel.history(after=start_of_week)]
        self_message_contents: str = '; '.join([message.content for message in messages if message.author == self.user])
        previous_attendees: List[str] = self_message_contents.split('; ')
        return previous_attendees

    async def start_recording(self):
        await self.alert_channel.send(f'<@{self.host.id}> Recording attendance in {self.event_channel.name}')
        self.recording = True
        [self.attendees.add(member) for member in self.event_channel.members]
