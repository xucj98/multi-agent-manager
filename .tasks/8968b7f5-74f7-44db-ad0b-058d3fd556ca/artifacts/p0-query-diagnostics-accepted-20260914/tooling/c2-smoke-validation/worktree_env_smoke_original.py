"""Check real SAPIEN rendering and the installed cuRobo CUDA extension."""

import json
from pathlib import Path

import iopath
import pytorch3d
import sapien.core as sapien
import torch

import curobo
from curobo.curobolib import geom_cu
from curobo.curobolib.geom import get_pose_distance


def render() -> tuple[int, ...]:
    engine = sapien.Engine()
    renderer = sapien.SapienRenderer()
    engine.set_renderer(renderer)
    scene = engine.create_scene()
    scene.add_ground(0.0)
    camera = scene.add_camera("worktree-smoke", 32, 32, 1.0, 0.1, 10.0)
    camera.entity.set_pose(sapien.Pose([0.0, -2.0, 1.0]))
    scene.step()
    scene.update_render()
    camera.take_picture()
    color = camera.get_picture("Color")
    if color.shape != (32, 32, 4) or not color.size:
        raise RuntimeError(f"unexpected SAPIEN color image: {color.shape}")
    return tuple(color.shape)


def curobo_distance() -> float:
    if "site-packages" not in str(Path(geom_cu.__file__).resolve()):
        raise RuntimeError(f"cuRobo extension is not from the venv: {geom_cu.__file__}")
    device = torch.device("cuda")
    shape = (1, 1)
    position = torch.zeros((*shape, 3), device=device)
    quaternion = torch.zeros((*shape, 4), device=device)
    quaternion[..., 0] = 1.0
    def zeros(size: tuple[int, ...]) -> torch.Tensor:
        return torch.zeros(size, device=device)
    out = get_pose_distance(
        zeros((1, 1, 1)),
        zeros((1, 1, 1)),
        zeros((1, 1, 1)),
        zeros((1, 1, 3)),
        zeros((1, 1, 4)),
        torch.zeros((1, 1, 1), device=device, dtype=torch.int32),
        position,
        position.clone(),
        quaternion,
        quaternion.clone(),
        torch.ones(6, device=device),
        torch.ones(4, device=device),
        torch.zeros(2, device=device),
        torch.ones((1, 1), device=device),
        torch.zeros(6, device=device),
        torch.zeros(6, device=device),
        torch.ones(1, device=device),
        torch.zeros((1, 1), device=device, dtype=torch.int32),
        torch.tensor([True], device=device, dtype=torch.uint8),
        1,
        1,
        1,
        1,
        False,
        False,
        True,
    )
    torch.cuda.synchronize(device)
    distance = float(out[0].abs().max().item())
    if not torch.isfinite(out[0]).all() or distance > 1e-5:
        raise RuntimeError(f"cuRobo pose distance failed: {out[0]}")
    return distance


if not torch.cuda.is_available():
    raise RuntimeError("Torch CUDA is unavailable; choose a visible idle GPU")
render_shape = render()
distance = curobo_distance()
print(
    json.dumps(
        {
            "curobo": getattr(curobo, "__version__", "unknown"),
            "curobo_extension": str(Path(geom_cu.__file__).resolve()),
            "iopath": str(Path(iopath.__file__).resolve()),
            "pytorch3d": str(Path(pytorch3d.__file__).resolve()),
            "render_shape": render_shape,
            "pose_distance_max": distance,
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(),
        },
        sort_keys=True,
    )
)
