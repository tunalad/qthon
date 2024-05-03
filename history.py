# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=multiple-imports
import os, shutil
from time import time
from pprint import pprint


class History:
    def __init__(self):
        super().__init__()
        self.temp_dir = None
        self.state = [{"time": time(), "list-state": []}]
        self.position_callback = None
        self.position = 1

    @property
    def position(self):
        """The position property."""
        return self._position
    @position.setter
    def position(self, value):
        self._position = value
        if self.position_callback:
            self.position_callback()

    def set_temp_dir(self, temp_dir):
        self.temp_dir = temp_dir
        self.SNAPSHOTS = os.path.join(temp_dir, "snapshots")

        if not os.path.exists(self.SNAPSHOTS):
            os.makedirs(self.SNAPSHOTS)

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
            current_time = time()

            if len(self.state) != self.position:
                # clear any future if exists
                self.state = self.state[: (len(self.state) - self.position)]

            self.state.append({"time": current_time, "list-state": new_state})
            self.position = len(self.state)

            self.take_snapshot(str(current_time))
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

    def take_snapshot(self, snap_name):
        """
        takes a snapshot of the current state and saves it in the snapshots folder
        """
        try:
            if not self.temp_dir:
                raise ValueError("temp_dir path is not set")

            snap_dir = os.path.join(self.SNAPSHOTS, snap_name)
            os.makedirs(snap_dir, exist_ok=True)

            snap_state = self.state[self.position - 1]["list-state"]

            for idx, item in enumerate(snap_state):
                file_path = item.get("path")
                if file_path:
                    # Extract filename from path
                    filename = os.path.basename(file_path)
                    # Destination path for the copied file in the snapshot directory
                    dest_path = os.path.join(snap_dir, filename)
                    # Copy the file to the snapshot directory
                    shutil.copy(file_path, dest_path)
            #print(f"Snapshot '{snap_name}' made")
        except Exception as e:
            print(f"[History/take_snapshot] {e}")

    def load_snapshot(self, snap_name):
        """
        loads a snapshot by copying its contents back to the current state
        """
        try:
            if not self.temp_dir:
                raise ValueError("temp_dir path is not set")

            snap_dir = os.path.join(self.SNAPSHOTS, snap_name)
            if not os.path.exists(snap_dir):
                #print(f"Snapshot '{snap_name}' does not exist")
                return

            # remove shyt (except the snaps dir)
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path) and filename != "snapshots":
                    print(file_path)
                    os.remove(file_path)

            # copy shyt
            for filename in os.listdir(snap_dir):
                src_path = os.path.join(snap_dir, filename)
                dest_path = os.path.join(self.temp_dir, filename)
                shutil.copy(src_path, dest_path)

            #print(f"Snapshot '{snap_name}' loaded")
        except Exception as e:
            print(f"[History/load_snapshot] {e}")
