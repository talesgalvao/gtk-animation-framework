# -*- coding: utf-8 -*-
import gtk
import gobject

class StepError(Exception):
    pass

class AnimationError(Exception):
    pass

class _GtkAnimationSteps(gobject.GObject):
    def __init__(self, parent):
        self.__gobject_init__()
        self.parent = parent 
        self._to = None
        self.acceleration = 1.0
        self.factor = 1

    def is_step_end(self):
        return self.parent.value >= self.to

    def reset(self):
        self._factor = self._original_factor

    @property
    def to(self):
        return self._to



    @to.setter
    def to(self, value):
        if type(value) not in (int, float):
            raise TypeError, "Value must be a number."
        self._to = value
        
    @property
    def acceleration(self):
        return self._acceleration

    @acceleration.setter
    def acceleration(self, value):
        if type(value) not in (int, float):
            raise TypeError, "Value must be a number."
        self._acceleration = float(value)

    @property
    def factor(self):
        return self._factor

    @factor.setter
    def factor(self, value):
        if type(value) not in (int, float):
            raise TypeError, "Value must be a number."
        try:
            self._original_factor
        except:
            self._original_factor = int(value)
        self._factor = int(value)


class GtkAnimation(gobject.GObject):
    """Gtk2 Animation framework with some facilities"""
    def __init__(self, interval=0.3, from_=None, 
                 to=None, acceleration=None):
        self.__gobject_init__()
        self.timer = None
        self.steps = []
        self._reload_iteration = 0
        self._callback = None
        self.value = None
        self.current_step = None
        if any((to, acceleration)): 
            if not all((to, acceleration)):
                raise TypeError, "you must set acceleration and to parameters together, or none of them."
            else:
                step = self.step()
                step.to = to
                step.acceleration = acceleration
        self.interval = interval

        self._start_value = from_

    def set_function(self, function):
        assert callable(function)
        self._callback = function

    @property
    def start_value(self):
        return self._start_value

    @start_value.setter
    def start_value(self, value):
        if type(value) not in (int, float):
            raise TypeError, "Value must be a number."
        self._start_value = value
       
    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        if type(value) not in (int, float):
            raise TypeError, "Value must be a number."
        self._interval = float(value)

    @property
    def times(self):
        return _times

    @times.setter
    def times(self, value):
        if type(value) is not int and value > 0:
            raise TypeError, "value must be an integer greater than 0."

        self.connect("animation-stop", self.reload)
        self._times = value

    def reload(self, *args):
        if self._reload_iteration < self._times:
            self._reload_iteration += 1
            self.start()

    def step(self):
        step = _GtkAnimationSteps(self) 
        self.steps.append(step)
        return step

    def _validate_step(self, step):
        if all([step.acceleration, step.to]):
            return True
        else:
            raise StepError, "Incomplete step #%d (%s)" % (
                                    self.steps.index(step),
                                    step
                                    )
    def start(self):
        self.reset()
        map(self._validate_step, self.steps)
        if not callable(self._callback):
            raise AnimationError, "do self.set_function, before start."
        if not len(self.steps):
            raise AnimationError, "we need at least one step."
        if self.start_value is None:
            raise AnimationError, "animation needs an start value."
        self.current_step = (0, self.steps[0])
        self.value = self.start_value
        self._iteration()

    def reset(self):
        if self.timer is not None:
            gobject.source_remove(self.timer)
        self.value = self.start_value
        self.current_step =(0, self.steps[0])
        map(lambda x: x.reset(), self.steps)

    def _iteration(self):
        self._callback(self.value)
        print self.value, "iteration"
        step_index, step = self.current_step
        if step.is_step_end():
            
            return self._next_step()
        step.factor *= step.acceleration
        if self.interval >= 0.01:
            self.interval /= step.acceleration
        print self.interval
        if self.timer:
            gobject.source_remove(self.timer)

        self.value += step.factor
        if step.is_step_end():
            self._next_step()
        self.timer = gobject.timeout_add(int(self.interval * 1000),
                                          self._iteration)
        
    def _next_step(self):
        step_index, step = self.current_step
        step_index+=1
        try:
            
            self.current_step = (step_index, self.steps[step_index])
            self._iteration()
        except IndexError:
            self.emit('animation-stop')
    

gobject.type_register(_GtkAnimationSteps)
gobject.type_register(GtkAnimation)

gobject.signal_new("step-end", _GtkAnimationSteps,
                    gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                    ())

gobject.signal_new("animation-stop", GtkAnimation,
                    gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                    ())

if __name__ == '__main__':
    w = gtk.Window()
    anim = GtkAnimation()
    anim.start_value = 50
    step0 = anim.step()
    step0.acceleration = 1.09 # accelerates 20% per iteration
    step0.to = 200
    step1 = anim.step()
    step1.acceleration = 0.7
    step1.to = 130
    step2 = anim.step()
    step2.acceleration = 0.8
    step2.to = 50
    anim.times = 3
    
    def a(anim):
        print "animatino stopped"

    anim.connect("animation-stop", a)

    def resize(x):
        screen = gtk.gdk.screen_get_default()
        w.resize(x, x)
        _,_, sw, sh = screen.get_monitor_geometry(0)
        new_left = int((sw/2.) - (x/2.))
        new_top = int((sh/2.) - (x/2.))
        w.move(new_left, new_top)

    anim.set_function(resize)
    w.show()
    anim.start()
    gtk.main()
