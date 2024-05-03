import sys
sys.path.insert(0, "/opt/tinybox/screen/")

from display import Display
from socketserver import UnixStreamServer, StreamRequestHandler
import threading, time, signal, os, random
from enum import Enum
from abc import ABC, abstractmethod
from queue import Queue
import pygame as pg

class Displayable(ABC):
  @abstractmethod
  def display(self, display: Display) -> None: pass

class Text(Displayable):
  def __init__(self, text: str): self.text = text
  def display(self, display: Display):
    # split text into lines
    lines = self.text.split("\n")
    starting_offset = 225 - (80 * (len(lines) - 1)) // 2
    for i, line in enumerate(lines):
      text = display.text(line, 100, True, (255, 255, 255))
      display.blit(text, (400 - text.get_width() // 2, starting_offset + (120 - text.get_height() // 2) + i * 80))

class AText(Displayable):
  def __init__(self, text_states: list[str]): self.text_states, self.current_state = text_states, 0
  def display(self, display: Display):
    text = display.text(self.text_states[self.current_state], 100, True, (255, 255, 255))
    display.blit(text, (400 - text.get_width() // 2, 225 + (120 - text.get_height() // 2)))
    self.current_state = (self.current_state + 1) % len(self.text_states)

class PositionableText(Displayable):
  def __init__(self, text: str, xy: tuple[int, int], size: int):
    self.text, self.x, self.y, self.size = text, xy[0], xy[1], size
  def display(self, display: Display):
    text = display.text(self.text, self.size, True, (255, 255, 255))
    display.blit(text, (self.x - text.get_width() // 2, self.y - text.get_height() // 2))

class VerticalProgressBar(Displayable):
  def __init__(self, value: float, max_value: float, width: int, height: int, x: int):
    self.value, self.max_value, self.width, self.height, self.x = value, max_value, width, height, x
  def display(self, display: Display):
    # draw background
    background = pg.Surface((self.width, self.height))
    pg.draw.rect(background, (20, 20, 20), (0, 0, self.width, self.height))
    display.blit(background, (self.x - self.width // 2, 240 - self.height // 2))
    # draw bar
    bar_height = self.height * self.value // self.max_value
    color_sub = 255 - ((self.value / self.max_value) * 255)
    bar = pg.Surface((self.width, bar_height))
    pg.draw.rect(bar, (255, color_sub, color_sub), (0, 0, self.width, bar_height))
    display.blit(bar, (self.x - self.width // 2, 240 - bar_height // 2))

class Image(Displayable):
  def __init__(self, path: str, xy: tuple[int, int], scale: tuple[int, int]):
    self.image = pg.image.load(path)
    self.image = pg.transform.scale(self.image, scale)
    self.x, self.y = xy
  def display(self, display: Display): display.blit(self.image, (self.x, self.y))

def lerp(a: float, b: float, t: float) -> float: return a + (b - a) * t
class LerpedImage(Displayable):
  def __init__(self, path: str, start_xy: tuple[int, int], end_xy: tuple[int, int], start_scale: tuple[int, int], end_scale: tuple[int, int], duration: int):
    self.image = pg.image.load(path)
    self.start_xy, self.end_xy, self.start_scale, self.end_scale, self.duration, self.t = start_xy, end_xy, start_scale, end_scale, duration, 0
  def display(self, display: Display):
    xy = (int(lerp(self.start_xy[0], self.end_xy[0], self.t)), int(lerp(self.start_xy[1], self.end_xy[1], self.t)))
    scale = (int(lerp(self.start_scale[0], self.end_scale[0], self.t)), int(lerp(self.start_scale[1], self.end_scale[1], self.t)))
    image = pg.transform.scale(self.image, scale)
    display.blit(image, xy)
    self.t = min(1, self.t + 1 / self.duration)

class DVDImage(Displayable):
  def __init__(self, path: str, scale: tuple[int, int], speed: float = 2):
    self.image = pg.image.load(path)
    self.image = pg.transform.scale(self.image, scale)
    self.x_speed, self.y_speed = speed, speed
    self.reset()
  def display(self, display: Display):
    if self.x + self.image.get_width() > 800 or self.x < 0: self.x_speed *= -1
    if self.y + self.image.get_height() > 480 or self.y < 0: self.y_speed *= -1
    self.x += self.x_speed
    self.y += self.y_speed
    display.blit(self.image, (self.x, self.y))
  def reset(self): self.x, self.y = random.randint(0, 800 - self.image.get_width()), random.randint(0, 480 - self.image.get_height())

def get_gpu_utilizations() -> list[float]:
  gpu_utilizations = []
  for i in range(1, 7):
    with open(f"/sys/class/drm/card{i}/device/gpu_busy_percent", "r") as f:
      gpu_utilizations.append(int(f.read().strip()))
  return gpu_utilizations

def get_gpu_power_draw() -> list[int]:
  gpu_power_draws = []
  for i in range(1, 7):
    with open(f"/sys/class/drm/card{i}/device/hwmon/hwmon{i+4}/power1_average", "r") as f:
      gpu_power_draws.append(int(f.read().strip()) // 1000000)
  return gpu_power_draws

DisplayState = Enum("DisplayState", ["TEXT", "STATUS"])
control_queue = Queue()
display_thread_alive = True
def display_thread():
  # initialize display
  display = Display("/dev/ttyACM0")
  display.clear()
  display.flip()

  # load assets
  logo = Image("/opt/tinybox/screen/logo.png", (200, 25), (400, 240))
  logo_sleep = DVDImage("/opt/tinybox/screen/logo.png", (400, 240))

  display_state = DisplayState.TEXT
  display_last_active = time.monotonic()
  to_display: Displayable | None = None

  while display_thread_alive:
    if not control_queue.empty():
      command, args = control_queue.get()
      print(f"[DT] Received command {command} with args {args}")
      if command == "text":
        display_state = DisplayState.TEXT
        to_display = args
      elif command == "state":
        display_state = DisplayState.STATUS
        display_last_active = time.monotonic()
    else:
      # reset display state if inactive for 15 seconds
      if time.monotonic() - display_last_active > 15 and display_state == DisplayState.STATUS:
        print("[DT] Display inactive for 15 seconds, switching back to sleep text state")
        display_state, to_display = DisplayState.TEXT, None
        display_last_active = time.monotonic()
        logo_sleep.reset()

      # check if display should be in status state
      gpu_utilizations = get_gpu_utilizations()
      print(f"[DT] GPU Utilizations: {gpu_utilizations}")
      mean_gpu_utilization = sum(gpu_utilizations) / len(gpu_utilizations)
      if mean_gpu_utilization > 5:
        display_state = DisplayState.STATUS
        display_last_active = time.monotonic()

      display.clear()
      if display_state == DisplayState.TEXT:
        if to_display is not None:
          logo.display(display)
          print(f"[DT] Displaying: {to_display}")
          to_display.display(display)
        else: logo_sleep.display(display)
      elif display_state == DisplayState.STATUS:
        for i, utilization in enumerate(gpu_utilizations):
          VerticalProgressBar(utilization, 100, 50, 380, 50 + 75 * i).display(display)
        power_draws = get_gpu_power_draw()
        total_power_draw = sum(power_draws)
        PositionableText(f"{total_power_draw}W", (625, 240), 100).display(display)

    # update display
    display.flip()

    # sleep
    # time.sleep(0.01)

class ControlHandler(StreamRequestHandler):
  def handle(self):
    data = self.rfile.readline().strip(b"\r\n").decode()
    command, *args = data.split(",")
    print(f"[CH] Received command {command} with args {args}")
    if command == "text":
      control_queue.put(("text", Text("\n".join(args))))
    elif command == "atext":
      control_queue.put(("text", AText(args)))
    elif command == "status":
      control_queue.put(("status", None))

if __name__ == "__main__":
  # start display thread
  dt = threading.Thread(target=display_thread)
  dt.start()

  # handle exit signals
  def signal_handler(sig, frame):
    print("[M] Exiting...")
    global display_thread_alive
    display_thread_alive = False
    os.remove("/run/tinybox-screen.sock")
    sys.exit(0)
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # start control server
  with UnixStreamServer("/run/tinybox-screen.sock", ControlHandler) as server:
    os.chmod("/run/tinybox-screen.sock", 0o777)
    server.serve_forever()
