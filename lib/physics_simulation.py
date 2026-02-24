import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import pymunk


class PhysicsSimulation:
    def __init__(self):
        self.gravity = 0, -9.820
        self.damping = 0.9999
        self.width, self.height = 16, 28
        self.e = 0.60  # Elasticity of objects.  Must be <=1.
        self.T = 16  # how long to simulate?
        self.dt = 1 / 300  # we simulate 300 timesteps per second
        self.subsampling = 10  # render one out of this number of timesteps.
        self.frames = self.T / self.dt / self.subsampling
        # Since we have 300 timesteps per second, 10 yields 30 fps. 5 yields 60 fps.
        self.dpi = 30  # use low values for preview. dpi=120 yields fullhd video if width,height are 16,9
        self.lowest_x, self.lowest_y = 0, 0
        self.columns = 0
        self.r = 0.1
        self.R = 0.2
        self.gap = self.r * 2 + self.R * 2 + 0.2

    def setup_space(self) -> tuple[pymunk.Space, list[pymunk.Body]]:
        space = pymunk.Space()
        space.gravity = self.gravity
        space.damping = self.damping
        static_body = space.static_body

        DYNAMIC_CATEGORY = 1  # 2⁰
        STATIC_CATEGORY = 2  # 2¹

        # Filter for dynamic shapes (only collides with static)
        dynamic_filter = pymunk.ShapeFilter(
            categories=DYNAMIC_CATEGORY,  # what I am
            mask=STATIC_CATEGORY  # what I collide with
        )

        # Filter for static shapes (collides with dynamic)
        # Usually you don't even need to set this one explicitly
        static_filter = pymunk.ShapeFilter(
            categories=STATIC_CATEGORY,
            mask=DYNAMIC_CATEGORY | DYNAMIC_CATEGORY  # can be just 0xFFFFFFFF too
        )

        static_lines = [
            # Bottom floor
            pymunk.Segment(static_body, (0, 0), (self.width, 0), 0.01),
            # Right wall
            # pymunk.Segment(static_body, (self.width - gap, gap), (self.width - gap, self.height * 100), 0.01),
            # Left wall
            # pymunk.Segment(static_body, (gap, gap), (gap, self.height * 100), 0.01),
            # pymunk.Segment(static_body, (0, self.height), (self.width / 2 - 1, self.height / 2), 0.01),
            # pymunk.Segment(static_body, (self.width, self.height), (self.width / 2 + 1, self.height / 2), 0.01),
            # pymunk.Segment(static_body, (0, 0), (self.width / 2 - 1, self.height / 2), 0.01),
            # pymunk.Segment(static_body, (self.width, 0), (self.width / 2 + 1, self.height / 2), 0.01),
        ]

        static_circles: list[pymunk.Circle] = []

        rows = 17
        cy = self.height - 1.5
        self.lowest_y = cy - (rows - 1) * self.gap * np.sqrt(3) / 2
        for row in range(rows):
            y = cy - row * self.gap * np.sqrt(3) / 2
            # row2 = rows - 1 + row % 2
            row2 = row + 2
            for col in range(row2 + 1):
                x = self.width / 2 - self.gap / 2 * row2 + self.gap * col
                shape = pymunk.Circle(static_body, self.r, (x, y))
                shape.elasticity = self.e
                shape.filter = static_filter
                static_circles.append(shape)
                if row == rows - 1:
                    static_lines.append(pymunk.Segment(static_body, (x, y), (x, 0), self.r))
                    if col == 0:
                        self.columns = row2
                        self.lowest_x = x

        # left_x = gap
        # left_y = gap + 1
        # h = 10
        # gap_y =
        # for y in np.arange(left_y, h, gap * np.sqrt(3)):
        #     for x in np.arange(left_x, self.width, gap):
        #         shape = pymunk.Circle(static_body, r, (x, y))
        #         shape.elasticity = self.e
        #         static_circles.append(shape)

        for line in static_lines:
            line.elasticity = self.e
            line.friction = 0
            line.filter = static_filter
        space.add(*static_lines, *static_circles)

        # random component of each ball's velocity (uniform)
        vrand = 0.5

        balls: list[pymunk.Body] = []
        np.random.seed(0)  # make sure that outputs of this function are repeatable

        # for row in range(rows):
        #     for col in range(cols):
        #         balls.append(self.mk_ball(
        #             x=cx + row * r * 2,
        #             y=cy + col * r * 2,
        #             vx=np.random.uniform(-vrand, +vrand),
        #             vy=np.random.uniform(-vrand, +vrand),
        #             radius=r,
        #             space=space
        #         ))

        for i in range(300):
            balls.append(self.mk_ball(
                x=self.width / 2,
                y=cy + self.r + self.R + 0.5,
                vx=np.random.uniform(-vrand, +vrand),
                vy=np.random.uniform(-vrand, +vrand),
                radius=self.R,
                shape_filter=dynamic_filter,
                space=space,
            ))

        return space, balls

    def mk_ball(self, x: float, y: float, vx: float, vy: float, radius: float, space: pymunk.Space,
                shape_filter: pymunk.ShapeFilter = None) -> pymunk.Body:
        body = pymunk.Body(0, 0)
        body.position = x, y
        body.velocity = vx, vy
        shape = pymunk.Circle(body, radius)
        shape.density = 1
        shape.elasticity = self.e
        shape.filter = shape_filter
        space.add(body, shape)
        body.radius = radius
        return body

    def simulate(self, space: pymunk.Space, balls: list[pymunk.Body]) -> \
            tuple[np.ndarray[tuple[int]], list[list[np.ndarray[tuple[any, ...]]]]]:
        ts = np.arange(0, self.T, self.dt)
        positions: list[list[np.ndarray[tuple[any, ...]]]] = []

        last_part = 0
        for t in ts:
            cur_part = t / self.T
            if cur_part - last_part >= 0.02:
                last_part = cur_part
                print(f'Simulation: {cur_part:.1%}')
            # log ball positions
            positions.append([np.array(b.position) for b in balls])
            # Step the simulation
            space.step(self.dt)
            for b in balls:
                if b in space.bodies:
                    # r = list(b.shapes)[0].radius
                    if b.position[1] < self.lowest_y:
                        shape = list(b.shapes)[0]
                        if shape.filter.categories == 1:
                            shape.filter = pymunk.ShapeFilter(group=0)
                        if b.position[1] < 0:
                            space.remove(b, shape)
            if len(space.bodies) == 0:  # no balls left in the simulation
                break
        return ts, positions

    def render(self):
        # Forward simulation
        space, balls = self.setup_space()
        ts, positions = self.simulate(space, balls)

        # # Backward simulation
        # space, balls = self.initialize()
        # # To simulate backwards, we invert the initial velocity of each ball
        # # and set the elasticity of each object to the reciprocal of the true value
        # for b in balls:
        #     s = list(b.shapes)[0]
        #     s.elasticity = 1 / s.elasticity
        #     b.velocity = -1 * b.velocity
        # for s in space.static_body.shapes:
        #     s.elasticity = 1 / s.elasticity
        # b_ts, b_positions = self.simulate(space, balls)
        #
        # # Stitch the resulting trajectories together
        # positions = b_positions[-1:0:-1] + f_positions

        # Prepare the figure and axes
        fig, ax = plt.subplots(figsize=(self.width, self.height), dpi=self.dpi)
        ax.set(xlim=[0, self.width], ylim=[0, self.height])
        ax.set_aspect("equal")
        ax.set_position((0, 0, 1, 1))
        fig.set(facecolor="y")

        # Prepare the patches for the balls
        cmap = plt.get_cmap("twilight")
        circles = [plt.Circle((0, 0), radius=b.radius, facecolor=cmap(i / len(balls))) for i, b in enumerate(balls)]
        [ax.add_patch(c) for c in circles]
        ax.set_facecolor((176 / 255, 196 / 255, 177 / 255))

        # Draw the walls as black lines
        for s in space.static_body.shapes:
            if isinstance(s, pymunk.Circle):
                ax.add_patch(plt.Circle((s.offset.x, s.offset.y), radius=s.radius, facecolor='black'))
            elif isinstance(s, pymunk.Segment):
                ax.plot([s.a.x, s.b.x], [s.a.y, s.b.y], linewidth=s.radius * 2 * self.dpi, color="k")

        # Animation function. This is called for each frame, passing an entry in positions
        cur_frame = [-3]
        circle_resolved = [False for _ in range(len(circles))]
        categories_count = [0 for _ in range(self.columns)]

        def drawframe(p: list[tuple[float, float]]):
            cur_frame[0] += 1
            if cur_frame[0] % 10 == 0:
                print(f'Frame: {cur_frame[0]}/{self.frames}')
            for i, c in enumerate(circles):
                if not circle_resolved[i] and p[i][1] < self.lowest_y:
                    circle_resolved[i] = True
                    category = int((p[i][0] - self.lowest_x) / self.gap)
                    if category < 0 or category >= self.columns:
                        continue
                    categories_count[category] += 1
                    c.set_facecolor(cmap(category * 30 + 100))
                c.set_center(p[i])
            return circles

        anim = animation.FuncAnimation(
            fig,
            drawframe,
            frames=positions[::self.subsampling],
            interval=self.dt * self.subsampling * 1000,
            blit=True,
        )

        # Set to True to save the animation to file
        print(f"Rendering {len(positions[::self.subsampling])} frames at {1 / (self.dt * self.subsampling)} fps")
        save = True
        if save:
            FFwriter = animation.FFMpegWriter(fps=int(1 / (self.dt * self.subsampling)))
            anim.save(
                "../data/video.mp4",
                writer=FFwriter,
            )
            plt.close(fig)
            print(f"Categories: {categories_count}")


physics_simulation = PhysicsSimulation()
physics_simulation.render()
