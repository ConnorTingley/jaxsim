from __future__ import annotations

import dataclasses
from typing import Any

import jax
import jax.numpy as jnp
import jax_dataclasses
import jaxopt

import jaxsim.api as js
import jaxsim.typing as jtp
from jaxsim.api.common import VelRepr
from jaxsim.math import Adjoint
from jaxsim.terrain.terrain import FlatTerrain, Terrain

from .common import ContactModel, ContactsParams, ContactsState


@jax_dataclasses.pytree_dataclass
class QuasiRigidContactParams(ContactsParams):
    """Parameters of the rigid contacts model."""

    # Time constant
    tau: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Adimensional damping coefficient
    xi: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Minimum impedance
    d_min: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Maximum impedance
    d_max: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Width
    width: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Midpoint
    midpoint: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Power exponent
    power: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Stiffness coefficient
    stiffness: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Damping coefficient
    damping: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.0, dtype=float)
    )

    # Friction coefficient
    mu: jtp.Float = dataclasses.field(
        default_factory=lambda: jnp.array(0.5, dtype=float)
    )

    def __hash__(self) -> int:
        from jaxsim.utils.wrappers import HashedNumpyArray

        return hash(
            (
                HashedNumpyArray(self.tau),
                HashedNumpyArray(self.xi),
                HashedNumpyArray(self.d_min),
                HashedNumpyArray(self.d_max),
                HashedNumpyArray(self.width),
                HashedNumpyArray(self.midpoint),
                HashedNumpyArray(self.power),
                HashedNumpyArray(self.stiffness),
                HashedNumpyArray(self.damping),
                HashedNumpyArray(self.mu),
            )
        )

    def __eq__(self, other: QuasiRigidContactParams) -> bool:
        return hash(self) == hash(other)

    @staticmethod
    def build(
        tau: jtp.Float = 0.01,
        xi: jtp.Float = 1.0,
        d_min: jtp.Float = 0.9,
        d_max: jtp.Float = 0.95,
        width: jtp.Float = 0.0001,
        midpoint: jtp.Float = 0.0,
        power: jtp.Float = 0.0,
        stiffness: jtp.Float = 0.0,
        damping: jtp.Float = 0.0,
        mu: jtp.Float = 0.5,
    ) -> QuasiRigidContactParams:
        """Create a `QuasiRigidContactParams` instance"""
        return QuasiRigidContactParams(mu=mu, stiffness=stiffness, damping=damping)

    @staticmethod
    def build_from_jaxsim_model(
        model: js.model.JaxSimModel,
        *,
        static_friction_coefficient: jtp.Float = 0.5,
        tau: jtp.Float = 0.01,
        xi: jtp.Float = 1.0,
        d_min: jtp.Float = 0.9,
        d_max: jtp.Float = 0.95,
        width: jtp.Float = 0.0001,
        midpoint: jtp.Float = 0.0,
        power: jtp.Float = 0.0,
        stiffness: jtp.Float = 0.0,
        damping: jtp.Float = 0.0,
        mu: jtp.Float = 0.5,
    ) -> QuasiRigidContactParams:
        """Build a `QuasiRigidContactParams` instance from a `JaxSimModel`."""

        return QuasiRigidContactParams.build(
            tau=tau,
            xi=xi,
            d_min=d_min,
            d_max=d_max,
            width=width,
            midpoint=midpoint,
            power=power,
            stiffness=stiffness,
            damping=damping,
            mu=mu,
        )

    def valid(self) -> bool:
        return bool(
            jnp.all(self.tau >= 0.0)
            and jnp.all(self.xi >= 0.0)
            and jnp.all(self.d_min >= 0.0)
            and jnp.all(self.d_max <= 1.0)
            and jnp.all(self.d_min <= self.d_max)
            and jnp.all(self.width >= 0.0)
            and jnp.all(self.midpoint >= 0.0)
            and jnp.all(self.power >= 0.0)
            and jnp.all(self.stiffness >= 0.0)
            and jnp.all(self.damping >= 0.0)
            and jnp.all(self.mu >= 0.0)
        )


@jax_dataclasses.pytree_dataclass
class QuasiRigidContactsState(ContactsState):
    """Class storing the state of the rigid contacts model."""

    def __eq__(self, other: QuasiRigidContactsState) -> bool:
        return hash(self) == hash(other)

    @staticmethod
    def build_from_jaxsim_model(
        model: js.model.JaxSimModel | None = None,
    ) -> QuasiRigidContactsState:
        """Build a `QuasiRigidContactsState` instance from a `JaxSimModel`."""
        return QuasiRigidContactsState.build()

    @staticmethod
    def build() -> QuasiRigidContactsState:
        """Create a `QuasiRigidContactsState` instance"""

        return QuasiRigidContactsState()

    @staticmethod
    def zero(model: js.model.JaxSimModel) -> QuasiRigidContactsState:
        """Build a zero `QuasiRigidContactsState` instance from a `JaxSimModel`."""
        return QuasiRigidContactsState.build()

    def valid(self, model: js.model.JaxSimModel) -> bool:
        return True


@jax_dataclasses.pytree_dataclass
class QuasiRigidContacts(ContactModel):
    """Rigid contacts model."""

    parameters: QuasiRigidContactParams = dataclasses.field(
        default_factory=QuasiRigidContactParams
    )

    terrain: jax_dataclasses.Static[Terrain] = dataclasses.field(
        default_factory=FlatTerrain
    )

    def compute_contact_forces(
        self,
        position: jtp.Vector,
        velocity: jtp.Vector,
        model: js.model.JaxSimModel,
        data: js.data.JaxSimModelData,
    ) -> tuple[jtp.Vector, tuple[Any, ...]]:

        def _detect_contact(x: jtp.Array, y: jtp.Array, z: jtp.Array) -> jtp.Array:
            x, y, z = jax.tree_map(jnp.squeeze, (x, y, z))

            n̂ = model.terrain.get_normal_at(x=x, y=y).squeeze()
            h = jnp.array([0, 0, z - model.terrain.get_height_at(x=x, y=y)])

            return jnp.array([0, 0, jnp.dot(h, n̂)], dtype=float)

        # Compute the activation state of the collidable points
        position = jax.vmap(_detect_contact)(*position.T)

        with data.switch_velocity_representation(VelRepr.Mixed):
            M = js.model.free_floating_mass_matrix(model=model, data=data)
            J_WC = jnp.vstack(
                jax.vmap(lambda j, height: j * (height < 0))(
                    js.contact.jacobian(model=model, data=data)[:, :3], position[:, 2]
                )
            )
            W_H_C = js.contact.transforms(model=model, data=data)
            h = js.model.free_floating_bias_forces(model=model, data=data)
            W_ν = data.generalized_velocity()
            J̇_WC = jnp.vstack(
                jax.vmap(lambda j, height: j * (height < 0))(
                    js.contact.jacobian_derivative(model=model, data=data)[:, :3],
                    position[:, 2],
                ),
            )

            a_ref, R = self._regularizers(
                model=model,
                parameters=self.parameters,
                position=position,
                velocity=velocity,
            )

        G = J_WC @ jnp.linalg.lstsq(M, J_WC.T)[0]

        CW_al_free_WC = J_WC @ jnp.linalg.lstsq(M, -h)[0] + J̇_WC @ W_ν

        # Calculate quantities for the linear optimization problem.
        A = G + R
        b = CW_al_free_WC - a_ref

        objective = lambda x: jnp.sum(jnp.square(A @ x + b))

        # Compute the 3D linear force in C[W] frame
        opt = jaxopt.LBFGS(
            fun=objective,
            maxiter=100,
            tol=1e-10,
            maxls=100,
            history_size=10,
            max_stepsize=100.0,
            stop_if_linesearch_fails=True,
        )

        CW_f_Ci = opt.run(init_params=jnp.zeros_like(b)).params.reshape(-1, 3)

        def mixed_to_inertial(W_H_C: jax.Array, CW_fl: jax.Array) -> jax.Array:
            W_Xf_CW = Adjoint.from_transform(
                W_H_C.at[0:3, 0:3].set(jnp.eye(3)),
                inverse=True,
            ).T
            return W_Xf_CW @ jnp.hstack([CW_fl, jnp.zeros(3)])

        W_f_C = jax.vmap(mixed_to_inertial)(W_H_C, CW_f_Ci)

        return W_f_C, None

    @staticmethod
    def _regularizers(
        model: js.model.JaxSimModel,
        parameters: jtp.Array,
        position: jtp.Array,
        velocity: jtp.Array,
    ) -> tuple:
        """Compute the contact jacobian and the reference acceleration.

        Args:
            model (JaxSimModel): The jaxsim model.
            position (jtp.Vector): The position of the collidable point.

        Returns:
            tuple: A tuple containing the contact jacobian, the reference acceleration, and the contact radius.
        """

        Ω, ζ, ξ_min, ξ_max, width, mid, p, K, D, μ = jax_dataclasses.astuple(parameters)

        def _imp_aref(
            position: jtp.Array,
            velocity: jtp.Array,
        ) -> tuple[jtp.Array, jtp.Array]:
            """Calculates impedance and offset acceleration in constraint frame.

            Args:
                position: position in constraint frame
                velocity: velocity in constraint frame

            Returns:
                impedance: constraint impedance
                a_ref: offset acceleration in constraint frame
            """
            imp_x = jnp.abs(position) / width
            imp_a = (1.0 / jnp.power(mid, p - 1)) * jnp.power(imp_x, p)

            imp_b = 1 - (1.0 / jnp.power(1 - mid, p - 1)) * jnp.power(1 - imp_x, p)

            imp_y = jnp.where(imp_x < mid, imp_a, imp_b)

            imp = jnp.clip(ξ_min + imp_y * (ξ_max - ξ_min), ξ_min, ξ_max)
            imp = jnp.atleast_1d(jnp.where(imp_x > 1.0, ξ_max, imp))

            # When passing negative values, K and D represent a spring and damper, respectively.
            K_f = jnp.where(K <= 0, -K / ξ_max**2, 1 / (ξ_max * Ω * ζ) ** 2)
            D_f = jnp.where(D <= 0, -D / ξ_max, 2 / (ξ_max * Ω))

            a_ref = -jnp.atleast_1d(D_f * velocity + K_f * imp * position)

            return imp, a_ref

        def _compute_row(
            *,
            link_idx: jtp.Float,
            position: jtp.Array,
            velocity: jtp.Array,
        ) -> tuple[jtp.Array, jtp.Array]:

            # Compute the reference acceleration.
            ξ, a_ref = _imp_aref(
                position=position,
                velocity=velocity,
            )

            # Compute the inverse inertia of the parent link.
            I = js.kin_dyn_parameters.LinkParameters.inertia_tensor(
                jax.tree_util.tree_map(
                    lambda l: l[link_idx], model.kin_dyn_parameters.link_parameters
                )
            )

            # Compute the regularization terms.
            R = (2 * μ**2 * (1 - ξ) / (ξ + 1e-12)) * (1 + μ**2) @ jnp.linalg.inv(I)

            return jax.tree.map(lambda x: x * (position[2] < 0), (a_ref, R))

        a_ref, R = jax.tree.map(
            jnp.concatenate,
            (
                *jax.vmap(_compute_row)(
                    link_idx=jnp.array(
                        model.kin_dyn_parameters.contact_parameters.body
                    ),
                    position=position,
                    velocity=velocity,
                ),
            ),
        )
        return a_ref, jnp.diag(R)
