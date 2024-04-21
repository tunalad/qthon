from time import time
from pprint import pprint


class History:
    """
    Class responsible for managing changes done to the current project/file
    """

    def __init__(self):
        super().__init__()
        self.state = [{"time": time(), "list-state": []}]
        self.position = 1

    def reset_state(self):
        """
        resets state to the default, empty, state
        """
        # no exceptions for this cuz there's no way this errors out somehow xddd
        self.state = [{"time": time(), "list-state": []}]
        self.position = 1

    def new_change(self, new_state):
        """
        when we make a change, we call this function and pass an array of the new state
        """
        try:
            if len(self.state) != self.position:
                # clear any future if exists
                self.state = self.state[: (len(self.state) - self.position)]

            self.state.append({"time": time(), "list-state": new_state})
            self.position = len(self.state)

            self.print_state()
        except Exception as e:
            print(f"[History.new_change] {e}")

    def undo(self, times=1):
        """
        we use this to go back in history
        """
        try:
            # no history
            if not len(self.state) > 1:
                print("we can't undo, there's no history going on")
                return

            # going back in history
            new_position = max(1, self.position - times)
            self.position = new_position

            self.print_state()
        except Exception as e:
            print(f"[History.undo] {e}")

    def redo(self, times=1):
        """
        we use this to go back in the future
        """
        try:
            if not len(self.state) > 1:
                print("we can't redo, there's no history going on")
                return

            # if moving to the future exceeds the length, just set us to the length
            new_pos = self.position + times
            if new_pos > len(self.state):
                self.position = len(self.state)
                print("we're in the future's future")
                return

            # yeah we can redo I think
            self.position += times

            self.print_state()
        except Exception as e:
            print(f"[History.redo] {e}")

    def print_state(self):
        return
        pprint(self.state[self.position - 1])
