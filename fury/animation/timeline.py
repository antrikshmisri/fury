from time import perf_counter
from fury.ui.elements import PlaybackPanel
from fury.animation.animation import Animation


class Timeline:
    """Keyframe animation Timeline.

    Timeline is responsible for handling the playback of keyframes animations.
    It has multiple playback options which makes it easy
    to control the playback, speed, state of the animation with/without a GUI
    playback panel.

    Attributes
    ----------
    animations : Animation or list[Animation], optional, default: None
        Actor/s to be animated directly by the Timeline (main Animation).
    playback_panel : bool, optional
        If True, the timeline will have a playback panel set, which can be used
        to control the playback of the timeline.
    length : float or int, default: None, optional
        the fixed length of the timeline. If set to None, the timeline will get
         its length from the animations that it controls automatically.
    loop : bool, optional
        Whether loop playing the timeline or play once.
    """

    def __init__(self, animations=None, playback_panel=False, loop=True,
                 length=None):

        self.playback_panel = None
        self._current_timestamp = 0
        self._speed = 1.0
        self._last_started_time = 0
        self._playing = False
        self._animations = []
        self._loop = loop
        self._length = length
        self._duration = length if length is not None else 0.0

        if playback_panel:
            def set_loop(is_loop):
                self._loop = is_loop

            def set_speed(speed):
                self.speed = speed

            self.playback_panel = PlaybackPanel(loop=self._loop)
            self.playback_panel.on_play = self.play
            self.playback_panel.on_stop = self.stop
            self.playback_panel.on_pause = self.pause
            self.playback_panel.on_loop_toggle = set_loop
            self.playback_panel.on_progress_bar_changed = self.seek
            self.playback_panel.on_speed_changed = set_speed

        if animations is not None:
            self.add_animation(animations)

    def update_duration(self):
        """Update and return the duration of the Timeline.

        Returns
        -------
        float
            The duration of the Timeline.
        """
        if self._length is not None:
            self._duration = self._length
        else:
            self._duration = max([0.0] + [anim.update_duration() for anim
                                          in self._animations])
        if self.has_playback_panel:
            self.playback_panel.final_time = self.duration
        return self.duration

    @property
    def duration(self):
        """Return the duration of the Timeline.

        Returns
        -------
        float
            The duration of the Timeline.
        """
        return self._duration

    def play(self):
        """Play the animation"""
        if not self.playing:
            if self.current_timestamp >= self.duration:
                self.current_timestamp = 0
            self._last_started_time = \
                perf_counter() - self._current_timestamp / self.speed
            self._playing = True

    def pause(self):
        """Pause the animation"""
        self._current_timestamp = self.current_timestamp
        self._playing = False

    def stop(self):
        """Stop the animation"""
        self._current_timestamp = 0
        self._playing = False
        self.update(force=True)

    def restart(self):
        """Restart the animation"""
        self._current_timestamp = 0
        self._playing = True
        self.update(force=True)

    @property
    def current_timestamp(self):
        """Get current timestamp of the Timeline.

        Returns
        -------
        float
            The current time of the Timeline.

        """
        if self.playing:
            self._current_timestamp = (perf_counter() -
                                       self._last_started_time) * self.speed
        return self._current_timestamp

    @current_timestamp.setter
    def current_timestamp(self, timestamp):
        """Set the current timestamp of the Timeline.

        Parameters
        ----------
        timestamp: float
            The time to set as current time of the Timeline.

        """
        self.seek(timestamp)

    def seek(self, timestamp):
        """Set the current timestamp of the Timeline.

        Parameters
        ----------
        timestamp: float
            The time to seek.

        """
        # assuring timestamp value is in the timeline range
        if timestamp < 0:
            timestamp = 0
        elif timestamp > self.duration:
            timestamp = self.duration
        if self.playing:
            self._last_started_time = \
                perf_counter() - timestamp / self.speed
        else:
            self._current_timestamp = timestamp
            self.update(force=True)

    def seek_percent(self, percent):
        """Seek a percentage of the Timeline's final timestamp.

        Parameters
        ----------
        percent: float
            Value from 1 to 100.

        """
        t = percent * self.duration / 100
        self.seek(t)

    @property
    def playing(self):
        """Return whether the Timeline is playing.

        Returns
        -------
        bool
            True if the Timeline is playing.
        """
        return self._playing

    @property
    def stopped(self):
        """Return whether the Timeline is stopped.

        Returns
        -------
        bool
            True if Timeline is stopped.

        """
        return not self.playing and not self._current_timestamp

    @property
    def paused(self):
        """Return whether the Timeline is paused.

        Returns
        -------
        bool
            True if the Timeline is paused.

        """

        return not self.playing and self._current_timestamp is not None

    @property
    def speed(self):
        """Return the speed of the timeline's playback.

        Returns
        -------
        float
            The speed of the timeline's playback.
        """
        return self._speed

    @speed.setter
    def speed(self, speed):
        """Set the speed of the timeline's playback.

        Parameters
        ----------
        speed: float
            The speed of the timeline's playback.

        """
        current = self.current_timestamp
        if speed <= 0:
            return
        self._speed = speed
        self._last_started_time = perf_counter()
        self.current_timestamp = current

    @property
    def loop(self):
        """Get loop condition of the timeline.

        Returns
        -------
        bool
            Whether the playback is in loop mode (True) or play one mode
            (False).
        """
        return self._loop

    @loop.setter
    def loop(self, loop):
        """Set the timeline's playback to loop or play once.

        Parameters
        ----------
        loop: bool
            The loop condition to be set. (True) to loop the playback, and
            (False) to play only once.
        """
        self._loop = loop

    @property
    def has_playback_panel(self):
        """Return whether the `Timeline` has a playback panel.

        Returns
        -------
        bool: 'True' if the `Timeline` has a playback panel. otherwise, 'False'
        """
        return self.playback_panel is not None

    def add_animation(self, animation):
        """Add Animation or list of Animations.

        Parameters
        ----------
        animation: Animation or list[Animation] or tuple[Animation]
            Animation/s to be added.
        """
        if isinstance(animation, (list, tuple)):
            [self.add_animation(anim) for anim in animation]
        elif isinstance(animation, Animation):
            animation._timeline = self
            self._animations.append(animation)
            self.update_duration()
        else:
            raise TypeError(f"Expected an Animation, a list or a tuple.")

    @property
    def animations(self) -> 'list[Animation]':
        """Return a list of Animations.

        Returns
        -------
        list:
            List of Animations controlled by the timeline.
        """
        return self._animations

    def update(self, force=False):
        """Update the timeline.

        Update the Timeline and all the animations that it controls. As well as
        the playback of the Timeline (if exists).

        Parameters
        ----------
        force: bool, optional, default: False
            If True, the timeline will update even when the timeline is paused
            or stopped and hence, more resources will be used.

        """
        time = self.current_timestamp
        if self.has_playback_panel:
            self.playback_panel.current_time = time
        if time > self.duration:
            if self._loop:
                self.seek(0)
            else:
                self.seek(self.duration)
                # Doing this will pause both the timeline and the panel.
                if self.has_playback_panel:
                    self.playback_panel.pause()
                else:
                    self.pause()
        if self.playing or force:
            [anim.update_animation(time) for anim in self._animations]

    def add_to_scene(self, ren):
        """Add this Timeline and all of its Animations to the scene"""
        if self.has_playback_panel:
            self.playback_panel.add_to_scene(ren)
        [ren.add(animation) for animation in self._animations]
