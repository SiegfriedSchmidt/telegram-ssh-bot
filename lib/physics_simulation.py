from matplotlib import animation
import numpy as np
import matplotlib.pyplot as plt
import pymunk
import math


class PhysicsSimulation:
    def __init__(self):
        self.space_gravity = 0, -9.81
        self.space_damping = 0.995
        self.space_threaded = False
        self.space_threads = 1
        self.width, self.height = 18, 14
        self.e = 0.3  # Elasticity of objects.  Must be <=1.
        self.friction = 0.2
        self.T = 14  # how long to simulate?
        self.dt = 1 / 300  # we simulate 300 timesteps per second
        self.subsampling = 10  # render one out of this number of timesteps.
        self.dpi = 40  # use low values for preview. dpi=120 yields fullhd video if width,height are 16,9
        self.r = 0.15
        self.R = 0.2
        self.gap = self.r * 2 + self.R * 2 + 0.2
        self.v_rand = 0
        self.pos_rand = 0
        self.rows = 16
        self.balls_count = 1
        self.lowest_x, self.lowest_y, self.columns = 0, 0, 0

        seed = np.random.randint(2 ** 63 - 1)
        print(f'seed: {seed}')
        self.random = np.random.default_rng(seed)

    def setup_space(self) -> tuple[pymunk.Space, list[pymunk.Body]]:
        space = pymunk.Space(threaded=self.space_threaded)

        space.gravity = self.space_gravity
        space.damping = self.space_damping
        space.threads = self.space_threads
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
            mask=DYNAMIC_CATEGORY  # can be just 0xFFFFFFFF too
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

        cy = self.height - 1.5
        self.lowest_y = cy - (self.rows - 1) * self.gap * np.sqrt(3) / 2
        for row in range(self.rows):
            y = cy - row * self.gap * np.sqrt(3) / 2
            # row2 = rows - 1 + row % 2
            row2 = row
            for col in range(row2 + 1):
                x = self.width / 2 - self.gap / 2 * row2 + self.gap * col
                shape = pymunk.Circle(static_body, self.r, (x, y))
                shape.elasticity = self.e
                shape.friction = self.friction
                shape.filter = static_filter
                shape.collision_type = STATIC_CATEGORY
                static_circles.append(shape)
                if row == self.rows - 1:
                    static_lines.append(pymunk.Segment(static_body, (x, y), (x, 0), self.r))
                    if col == 0:
                        self.columns = row2
                        self.lowest_x = x

        for line in static_lines:
            # line.elasticity = self.e
            line.friction = 0.5
            line.filter = static_filter
        space.add(*static_lines, *static_circles)

        balls: list[pymunk.Body] = []

        for i in range(self.balls_count):
            body = pymunk.Body(0, 0)
            body.position = (
                self.width / 2 + self.random.uniform(-self.pos_rand, self.pos_rand),
                cy + self.r + self.R + 1
            )
            body.velocity = self.random.uniform(-self.v_rand, self.v_rand), 0
            body.radius = self.R

            shape = pymunk.Circle(body, self.R)
            shape.density = 1
            shape.elasticity = self.e
            shape.friction = self.friction
            shape.filter = dynamic_filter
            shape.collision_type = DYNAMIC_CATEGORY

            space.add(body, shape)
            balls.append(body)

        decided = set()

        # path_idx = [0]
        # path = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        def ball_hit(arbiter: pymunk.Arbiter, space: pymunk.Space, data: any):
            ball, peg = arbiter.shapes
            peg_pos: pymunk.Vec2d = peg.offset

            pair_id = (peg_pos, ball.body.id)
            if pair_id not in decided:
                choice = 1 if self.random.uniform(0, 1) > 0.5 else -1
                # choice = path[path_idx[0]]
                # path_idx[0] += 1
                ball.body.velocity = (1 * choice, 0)
                decided.add(pair_id)
            return

        space.on_collision(DYNAMIC_CATEGORY, STATIC_CATEGORY, pre_solve=ball_hit)
        return space, balls

    def simulate(self, space: pymunk.Space, balls: list[pymunk.Body]) -> \
            tuple[list[list[np.ndarray[tuple[any, ...]]]], list[int], list[int]]:
        positions: list[list[np.ndarray[tuple[any, ...]]]] = []
        ball_category = [0 for _ in range(len(balls))]
        categories_count = [0 for _ in range(self.columns + 2)]
        resolved_count = 0

        last_part = 0
        for t in np.arange(0, self.T, self.dt):
            cur_part = t / self.T
            if cur_part - last_part >= 0.02:
                last_part = cur_part
                print(f'Simulation: {cur_part:.1%}, resolved: {resolved_count}')
            # log ball positions
            positions.append([np.array(b.position) for b in balls])
            # Step the simulation
            space.step(self.dt)
            for i, b in enumerate(balls):
                if b in space.bodies:
                    if not ball_category[i] and b.position[1] + self.R < self.lowest_y:
                        x_with_offset = b.position[0] - self.lowest_x
                        category = int(x_with_offset / self.gap) + 2
                        if x_with_offset < 0:
                            category = 1
                        elif category >= self.columns + 2:
                            category = self.columns + 2

                        ball_category[i] = category
                        categories_count[category - 1] += 1
                        resolved_count += 1

                        # shape = list(b.shapes)[0]
                        # shape.filter = pymunk.ShapeFilter(group=0)
                    if b.position[1] < 0:
                        shape = list(b.shapes)[0]
                        space.remove(b, shape)
            if len(space.bodies) == 0 or resolved_count == len(balls):
                break
        return positions, ball_category, categories_count

    @staticmethod
    def calculate_dist_params(probabilities: np.ndarray, values: np.ndarray = None) -> tuple[float, float]:
        if values is None:
            values = np.arange(probabilities.size)
        E = np.sum(values * probabilities)
        E2 = np.sum(values ** 2 * probabilities)
        Var = E2 - E ** 2
        return E, Var

    def render(self):
        # Forward simulation
        space, balls = self.setup_space()
        positions, ball_category, categories_count = self.simulate(space, balls)

        categories_count = np.array(categories_count)
        resolved_count = np.sum(categories_count)
        probabilities = categories_count / resolved_count
        E, Var = self.calculate_dist_params(probabilities)
        Expected_Var = self.rows * 0.5 * 0.5
        print(
            f"{len(categories_count)=}\n{resolved_count=}\n{categories_count=}\n{probabilities=}\n{E=}\n{Var=}\n{Expected_Var=}"
        )

        bin_probabilities = np.zeros_like(probabilities)
        for x in range(1, bin_probabilities.size - 1):
            bin_probabilities[x] = math.comb(self.rows, x) * 0.5 ** self.rows
        bin_probabilities[0] = (1 - np.sum(bin_probabilities)) / 2
        bin_probabilities[-1] = bin_probabilities[0]

        bin_E, bin_Var = self.calculate_dist_params(bin_probabilities)
        coefficients = 1 / bin_probabilities / bin_probabilities.size
        print('IDEAL coefficients:', list(map(float, coefficients)))

        coefficients = np.array([
            500, 450, 30, 9, 3, 1, 0.5, 0.2, 0, 0.2, 0.5, 1, 3, 9, 30, 450, 500
        ])
        print(coefficients * bin_probabilities)
        coef_E, coef_Var = self.calculate_dist_params(bin_probabilities, coefficients)
        bin_probabilities = list(map(float, bin_probabilities))
        coefficients = list(map(float, coefficients))
        print(f"{coefficients=}\n{bin_probabilities=}\n{coef_E=}\n{coef_Var=}\n{bin_E=}\n{bin_Var=}")

        # Prepare the figure and axes
        fig, ax = plt.subplots(figsize=(self.width, self.height), dpi=self.dpi)
        ax.set(xlim=[0, self.width], ylim=[0, self.height])
        ax.set_aspect("equal")
        ax.set_position((0, 0, 1, 1))
        fig.set(facecolor="y")

        # Prepare the patches for the balls
        cmap = plt.get_cmap("viridis")
        circles = [
            plt.Circle(
                xy=(0, 0),
                radius=b.radius,
                facecolor=cmap((ball_category[i] - 1) / (len(categories_count) - 1)) if ball_category[
                                                                                            i] != 0 else "black"
            ) for i, b in enumerate(balls)
        ]
        [ax.add_patch(c) for c in circles]
        ax.set_facecolor((176 / 255, 196 / 255, 177 / 255))

        # Draw the walls as black lines
        for s in space.static_body.shapes:
            if isinstance(s, pymunk.Circle):
                ax.add_patch(plt.Circle((s.offset.x, s.offset.y), radius=s.radius, facecolor='black'))
            elif isinstance(s, pymunk.Segment):
                ax.plot([s.a.x, s.b.x], [s.a.y, s.b.y], linewidth=s.radius * self.dpi, color="k")

        for i, coef in enumerate(coefficients[1:-1]):
            ax.text(
                self.lowest_x + self.gap * i + self.gap * 0.5, self.lowest_y - 0.5, f'{coef:g}',
                fontsize=21,
                color='green',
                fontweight='bold',
                horizontalalignment='center',
                verticalalignment='center'
            )

        # Animation function. This is called for each frame, passing an entry in positions
        cur_frame = [-3]
        frames_count = int(len(positions) / self.subsampling)

        def drawframe(p: list[tuple[float, float]]):
            cur_frame[0] += 1
            if cur_frame[0] % 10 == 0:
                print(f'Frame: {cur_frame[0]}/{frames_count}')
            for i, c in enumerate(circles):
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
        return coefficients[ball_category[0] - 1]


physics_simulation = PhysicsSimulation()

if __name__ == '__main__':
    print(physics_simulation.render())
