"""Planet Simulator"""

import math

import pygame
from pygame.locals import KEYDOWN, MOUSEMOTION, MOUSEWHEEL, RESIZABLE, VIDEORESIZE

WORLD_SCALE = 10_000_000  # 1 pixel = 10_000_000 meters = 10_000 km
WINDOW_SIZE = (800, 600)
CURRENT_POSITION = [
    WINDOW_SIZE[0] * WORLD_SCALE / 20000,
    WINDOW_SIZE[1] * WORLD_SCALE / 20000,
]  # Center (0, 0)
CURRENT_ZOOM = 0.001  # Start with a zoom level that makes both planets visible
FIXED_TIMESTEP = 60 * 60  # 1 hour per update (higher = less accurate but faster)
FPS = 60
GUI_UPDATE_RATE = FPS * 0.2  # Update the GUI every 0.2 seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (70, 70, 70)

# Constants
_G = 6.67430e-11  # Gravitational constant


class Planet:
    """Class representing a planet/star."""
    def __init__(
        self,
        name: str,
        mass: float,
        radius: float,
        position: tuple[float, float],
        velocity: tuple[float, float],
        color: tuple[int, int, int],
    ):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.position = position  # In world coordinates (scaled)
        self.velocity = velocity  # In meters per second
        self.color = color

    def draw(self, screen: pygame.surface.Surface) -> None:
        """Draw the planet on the screen."""
        x, y = world_to_screen(self.position[0], self.position[1])
        if x is not None:
            pygame.draw.circle(
                screen,
                self.color,
                (x, y),
                max(size_to_screen(self.radius), 2),
            )

    def update(self, planet_list: list["Planet"], timestep: float) -> None:
        """Update the position and velocity of the planet."""
        total_force_x, total_force_y = 0, 0

        for planet in planet_list:
            if planet == self:
                continue

            force_x, force_y = calculate_gravity(self, planet)
            total_force_x += force_x
            total_force_y += force_y

        # Update velocity based on total gravitational forces
        self.velocity[0] += (total_force_x / self.mass) * timestep
        self.velocity[1] += (total_force_y / self.mass) * timestep

        # Update position based on velocity
        self.position[0] += self.velocity[0] * timestep / WORLD_SCALE
        self.position[1] += self.velocity[1] * timestep / WORLD_SCALE


def world_to_screen(
    world_x: float, world_y: float, allow_offscreen: bool = False
) -> tuple[float, float]:
    """Convert world coordinates to screen coordinates."""
    position = [
        (world_x + CURRENT_POSITION[0]) * CURRENT_ZOOM,
        (world_y + CURRENT_POSITION[1]) * CURRENT_ZOOM,
    ]
    if not allow_offscreen and (
        position[0] < 0
        or position[1] < 0
        or position[0] > WINDOW_SIZE[0]
        or position[1] > WINDOW_SIZE[1]
    ):
        return None, None
    return position


def screen_to_world(screen_x: float, screen_y: float) -> tuple[float, float]:
    """Convert screen coordinates to world coordinates."""
    return [
        (screen_x / CURRENT_ZOOM) - CURRENT_POSITION[0],
        (screen_y / CURRENT_ZOOM) - CURRENT_POSITION[1],
    ]


def size_to_screen(size: float) -> float:
    """Convert a size in meters to pixels."""
    return size / WORLD_SCALE * CURRENT_ZOOM


def calculate_gravity(planet1: Planet, planet2: Planet) -> tuple[float, float]:
    """Calculate the gravitational force between two planets."""
    dx = (planet2.position[0] - planet1.position[0]) * WORLD_SCALE
    dy = (planet2.position[1] - planet1.position[1]) * WORLD_SCALE
    distance = math.sqrt(dx**2 + dy**2)
    if distance == 0:
        return 0, 0
    force = _G * planet1.mass * planet2.mass / distance**2
    angle = math.atan2(dy, dx)
    force_x = force * math.cos(angle)
    force_y = force * math.sin(angle)
    return force_x, force_y


def positions_to_angle(
    position1: tuple[float, float], position2: tuple[float, float]
) -> float:
    """Calculate the angle between two positions."""
    dx = position2[0] - position1[0]
    dy = position2[1] - position1[1]
    return math.atan2(dy, dx)


def draw_grid(
    screen,
    top_left: tuple[float, float],
    bottom_right: tuple[float, float],
    spacing: int,
    color: tuple[int, int, int],
) -> None:
    """Draw a grid on the screen."""
    # Snap grid lines to the nearest spacing interval
    start_x = (top_left[0] // spacing) * spacing
    end_x = (bottom_right[0] // spacing + 1) * spacing
    start_y = (top_left[1] // spacing) * spacing
    end_y = (bottom_right[1] // spacing + 1) * spacing

    # Draw vertical grid lines
    for x in range(int(start_x), int(end_x), spacing):
        screen_x, _ = world_to_screen(x, 0, allow_offscreen=True)
        if 0 <= screen_x <= WINDOW_SIZE[0]:  # Only draw if on screen
            pygame.draw.line(screen, color, (screen_x, 0), (screen_x, WINDOW_SIZE[1]))

    # Draw horizontal grid lines
    for y in range(int(start_y), int(end_y), spacing):
        _, screen_y = world_to_screen(0, y, allow_offscreen=True)
        if 0 <= screen_y <= WINDOW_SIZE[1]:  # Only draw if on screen
            pygame.draw.line(screen, color, (0, screen_y), (WINDOW_SIZE[0], screen_y))


def center_on_screen(position: tuple[float, float]) -> tuple[float, float]:
    """Center the view on the given position."""
    screen_pos = world_to_screen(position[0], position[1], True)
    centered_inverted = screen_to_world(
        screen_pos[0] - WINDOW_SIZE[0] / 2, screen_pos[1] - WINDOW_SIZE[1] / 2
    )
    return [-centered_inverted[0], -centered_inverted[1]]


def is_on_screen(world_pos: tuple[float, float]) -> bool:
    """Check if a world position is on the screen."""
    screen_pos = world_to_screen(world_pos[0], world_pos[1], False)
    return screen_pos[0] is not None


def draw_info(
    screen: pygame.surface.Surface, font: pygame.font.Font, planet: Planet
) -> None:
    """Draw the planet information on the screen."""
    x, y = world_to_screen(planet.position[0], planet.position[1])
    name_text = font.render(f"Name: {planet.name}", font, WHITE)
    position_text = font.render(
        f"Pos: ({round(planet.position[0])}, {round(planet.position[1])})", font, WHITE
    )
    velocity_text = font.render(
        f"Vel: {round(math.hypot(planet.velocity[0], planet.velocity[1]) * 0.001, 2)} km/s",
        font,
        WHITE,
    )
    screen.blit(name_text, (x + 20, y + 20))
    screen.blit(position_text, (x + 20, y + 50))
    screen.blit(velocity_text, (x + 20, y + 80))


def is_hovering(position: tuple[float, float], planet: Planet) -> bool:
    """Check if the mouse is hovering over a planet."""
    x, y = world_to_screen(planet.position[0], planet.position[1])
    return x is not None and math.hypot(x - position[0], y - position[1]) <= max(
        size_to_screen(planet.radius), 5
    )


def seconds_to_time(seconds: int) -> tuple[int, int, int, int, int, int]:
    """Convert seconds to a human-readable time format."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    months, days = divmod(days, 30)
    years, months = divmod(months, 12)
    return years, months, days, hours, minutes, seconds


def format_time(
    years: int, months: int, days: int, hours: int, minutes: int, seconds: int
) -> str:
    """Format the time components into a string."""
    formatted_time = ""
    if years:
        formatted_time += f"{years}y "
    if months:
        formatted_time += f"{months}m "
    if days:
        formatted_time += f"{days}d "
    if hours:
        formatted_time += f"{hours}h "
    if minutes:
        formatted_time += f"{minutes}m "
    if seconds:
        formatted_time += f"{seconds}s"
    return formatted_time


if __name__ == "__main__":
    planets = [
        Planet(
            "Sun",
            mass=1.989e30,
            radius=696340000,
            position=[0, 0],
            velocity=[0, 0],
            color=(255, 204, 0),  # Bright yellow
        ),  # Sun
        Planet(
            "Mercury",
            mass=3.302e23,
            radius=2439700,
            position=[5.791e10 / WORLD_SCALE, 0],
            velocity=[0, 47362],
            color=(123, 123, 123),  # Gray
        ),  # Mercury
        Planet(
            "Venus",
            mass=4.869e24,
            radius=6051800,
            position=[1.082e11 / WORLD_SCALE, 0],
            velocity=[0, 35020],
            color=(229, 194, 154),  # Light yellow
        ),  # Venus
        Planet(
            "Earth",
            mass=5.972e24,
            radius=6371000,
            position=[1.496e11 / WORLD_SCALE, 0],
            velocity=[0, 29780],
            color=(59, 92, 154),  # Blue
        ),  # Earth
        Planet(
            "Mars",
            mass=6.42e23,
            radius=3389500,
            position=[2.279e11 / WORLD_SCALE, 0],
            velocity=[0, 24077],
            color=(193, 68, 14),  # Red
        ),  # Mars
        Planet(
            "Jupiter",
            mass=1.898e27,
            radius=71492000,
            position=[7.783e11 / WORLD_SCALE, 0],
            velocity=[0, 13060],
            color=(209, 154, 106),  # Light brown
        ),  # Jupiter
        Planet(
            "Saturn",
            mass=5.684e26,
            radius=58232000,
            position=[1.427e12 / WORLD_SCALE, 0],
            velocity=[0, 10118],
            color=(209, 180, 140),  # Ligher brown
        ),  # Saturn
        Planet(
            "Uranus",
            mass=8.681e25,
            radius=25362000,
            position=[2.871e12 / WORLD_SCALE, 0],
            velocity=[0, 6810],
            color=(167, 198, 217),  # Light blue
        ),  # Uranus
        Planet(
            "Neptune",
            mass=1.024e26,
            radius=24622000,
            position=[4.497e12 / WORLD_SCALE, 0],
            velocity=[0, 5477],
            color=(75, 111, 154),  # Darker blue
        ),  # Neptune
    ]
    pygame.init()

    screen = pygame.display.set_mode(WINDOW_SIZE, RESIZABLE)
    pygame.display.set_caption("Planet Simulator")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    paused = False
    running = True
    timestep = 60 * 60 * 6  # 6h per update
    time_passed = 0
    physics_counter = 0
    gui_counter = GUI_UPDATE_RATE
    gui_text = []

    followed_planet = None
    hovered_planets = []

    while running:
        # Accumulate time passed
        time_passed += timestep
        physics_counter += timestep

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_w:
                    timestep *= 2
                elif event.key == pygame.K_s:
                    timestep /= 2
                elif event.key == pygame.K_c:
                    CURRENT_POSITION = [
                        WINDOW_SIZE[0] * WORLD_SCALE / 20000,
                        WINDOW_SIZE[1] * WORLD_SCALE / 20000,
                    ]
                    CURRENT_ZOOM = 0.001
            elif event.type == MOUSEWHEEL:
                # Nonlinear zoom
                zoom_factor = 0.001 if event.y > 0 else -0.001
                zoom_speed = 1
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    zoom_speed = 10
                if CURRENT_ZOOM > 0.01:
                    zoom_speed *= 5
                elif CURRENT_ZOOM > 0.1:
                    zoom_speed *= 25
                elif CURRENT_ZOOM > 0.5:
                    zoom_speed *= 50
                elif CURRENT_ZOOM > 1:
                    zoom_speed *= 100
                elif CURRENT_ZOOM > 10:
                    zoom_speed *= 200
                new_zoom = CURRENT_ZOOM + zoom_factor * zoom_speed
                new_zoom = max(0.001, min(new_zoom, 25))

                # Adjust the current position to zoom into the mouse position
                CURRENT_POSITION[0] -= mouse_x / CURRENT_ZOOM - mouse_x / new_zoom
                CURRENT_POSITION[1] -= mouse_y / CURRENT_ZOOM - mouse_y / new_zoom
                CURRENT_ZOOM = new_zoom
            elif event.type == MOUSEMOTION:
                # Use the right mouse button for dragging
                if event.buttons[2]:
                    CURRENT_POSITION[0] += event.rel[0] / CURRENT_ZOOM
                    CURRENT_POSITION[1] += event.rel[1] / CURRENT_ZOOM
                    # Stop following a planet when dragging
                    followed_planet = None

                hovered_planets = []
                for planet in planets:
                    x, y = world_to_screen(planet.position[0], planet.position[1])
                    if x is not None and is_hovering((mouse_x, mouse_y), planet):
                        is_planet_hovered = True
                        hovered_planets.append(planet)

            elif event.type == pygame.MOUSEBUTTONUP:
                # Follow a planet when clicking on it
                if event.button == 1:
                    followed_planet = None
                    for planet in planets:
                        x, y = world_to_screen(planet.position[0], planet.position[1])
                        if x is not None and is_hovering((mouse_x, mouse_y), planet):
                            followed_planet = planet
            elif event.type == VIDEORESIZE:
                # Adjust CURRENT_POSITION to maintain the same relative position
                CURRENT_POSITION[0] *= event.w / WINDOW_SIZE[0]
                CURRENT_POSITION[1] *= event.h / WINDOW_SIZE[1]

                # Handle window resizing
                WINDOW_SIZE = event.size
                screen = pygame.display.set_mode(WINDOW_SIZE, RESIZABLE)
                gui_counter = GUI_UPDATE_RATE  # Force GUI update

        # Draw the background
        screen.fill(BLACK)

        # Update the planets based on the fixed timestep
        while physics_counter >= FIXED_TIMESTEP:
            if not paused:
                for planet in planets:
                    planet.update(planets, FIXED_TIMESTEP)
            physics_counter -= FIXED_TIMESTEP

        # Center the view on the followed planet
        if followed_planet:
            CURRENT_POSITION = center_on_screen(followed_planet.position)

        # Draw the grid
        screen_top_left = screen_to_world(0, 0)
        screen_bottom_right = screen_to_world(WINDOW_SIZE[0], WINDOW_SIZE[1])
        draw_grid(
            screen, screen_top_left, screen_bottom_right, spacing=100000, color=GRAY
        )

        SCREEN_CENTER = screen_to_world(WINDOW_SIZE[0] / 2, WINDOW_SIZE[1] / 2)

        # Draw the planets
        for planet in planets:
            planet.draw(screen)
            # Render planet ESP if not on screen
            if not is_on_screen(planet.position):
                angle = positions_to_angle(SCREEN_CENTER, planet.position)
                direction_vector = (math.cos(angle), math.sin(angle))
                line_length = (
                    math.hypot(
                        planet.position[0] - SCREEN_CENTER[0],
                        planet.position[1] - SCREEN_CENTER[1],
                    )
                    / WORLD_SCALE
                    * 1000
                )
                offset = WINDOW_SIZE[0] / 8
                pygame.draw.line(
                    screen,
                    planet.color,
                    (
                        WINDOW_SIZE[0] / 2 + direction_vector[0] * offset,
                        WINDOW_SIZE[1] / 2 + direction_vector[1] * offset,
                    ),
                    (
                        WINDOW_SIZE[0] / 2
                        + direction_vector[0] * (offset + line_length)
                        + (direction_vector[0] * (offset / 10)),
                        WINDOW_SIZE[1] / 2
                        + direction_vector[1] * (offset + line_length)
                        + (direction_vector[1] * (offset / 10)),
                    ),
                    2,
                )

        if followed_planet:
            draw_info(screen, font, followed_planet)
            if followed_planet in hovered_planets:
                hovered_planets.remove(followed_planet)

        # Draw the hovered planet information
        for planet in hovered_planets:
            draw_info(screen, font, planet)

        # Draw the mouse coordinates and scale at full framerate
        world_mouse_x, world_mouse_y = screen_to_world(mouse_x, mouse_y)
        coordinates_text = font.render(
            f"({round(world_mouse_x / 1000, 2)}k, {round(world_mouse_y / 1000, 2)}k) - "
            f"({round(CURRENT_POSITION[0] / 1000, 2)}k, {round(CURRENT_POSITION[1] / 1000, 2)}k) - "
            f"{round(CURRENT_ZOOM, 4)} ",
            font,
            WHITE,
        )
        screen.blit(coordinates_text, (5, 5))

        gui_counter += 1
        # Update the GUI every GUI_UPDATE_RATE frames
        if gui_counter >= GUI_UPDATE_RATE:
            gui_text = []
            gui_counter = 0

            # Draw the current timestep
            timestep_text = font.render(
                f"Timestep: {format_time(*seconds_to_time(timestep))}", font, WHITE
            )
            gui_text.append((timestep_text, (5, 35)))

            # Draw the current FPS
            fps_text = font.render(f"{round(clock.get_fps())} FPS", font, WHITE)
            gui_text.append((fps_text, (5, 65)))

            # Draw the time passed
            time_passed_text = font.render(
                f"Time passed: {format_time(*seconds_to_time(time_passed))}",
                font,
                WHITE,
            )
            gui_text.append(
                (time_passed_text, (5, WINDOW_SIZE[1] - time_passed_text.get_height()))
            )

        # Update the GUI text
        for text, position in gui_text:
            screen.blit(text, position)

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
