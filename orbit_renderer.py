import os
import cv2
import time
import tqdm
import numpy as np
import dearpygui.dearpygui as dpg

import torch
import torch.nn.functional as F

import rembg

from utils.cam_utils import orbit_camera, OrbitCamera
from utils.gs_renderer import Renderer, MiniCam

from utils.grid_put import mipmap_linear_grid_put_2d
import wandb
from PIL import Image

import utils.image_utils as image_utils


def render_orbit_imgs(load_path):
    renderer = Renderer(sh_degree=0)
    renderer.initialize(load_path)
    poses = []
    # render from hor -180 to 180 per 20 degree
    for hor in range(-180, 180, 40):
        pose = orbit_camera(-15, hor, 3)
        poses.append(pose)

    fovy = 50
    for i, pose in enumerate(poses):
        # print(pose)
        cur_cam = MiniCam(
            pose,
            512,
            512,
            np.deg2rad(fovy),
            np.deg2rad(fovy),
            0.01,
            100,
        )
        bg_color = torch.tensor([1, 1, 1], dtype=torch.float32, device="cuda")
        out = renderer.render(cur_cam, bg_color=bg_color)
        img = out["image"].unsqueeze(0)[0]
        img = img.detach().permute(1, 2, 0).cpu().numpy()
        img = (img * 255).astype(np.uint8)
        img = Image.fromarray(img)
        img.save(f"renders/{i}.png")


def render_gif(load_path):
    renderer = Renderer(sh_degree=0)
    renderer.initialize(load_path)
    poses = []
    imgs = []
    depth_imgs = []
    for hor in range(-180, 179, 10):
        pose = orbit_camera(-15, hor, 3)
        poses.append(pose)

    fovy = 50
    for i, pose in enumerate(poses):
        # print(pose)
        cur_cam = MiniCam(
            pose,
            512,
            512,
            np.deg2rad(fovy),
            np.deg2rad(fovy),
            0.01,
            100,
        )
        bg_color = torch.tensor([1, 1, 1], dtype=torch.float32, device="cuda")
        out = renderer.render(cur_cam, bg_color=bg_color)
        img = out["image"].unsqueeze(0)[0]
        img = img.detach().permute(1, 2, 0).cpu().numpy()
        img = (img * 255).astype(np.uint8)
        imgs.append(img)
        depth_img = out["depth"].unsqueeze(0)[0]

        depth_img = depth_img.detach().cpu().numpy().reshape(512, 512)
        depth_imgs.append(depth_img)
    # use imageio to create gif loop
    import imageio

    depth_imgs = (depth_imgs / np.max(depth_imgs) * 255).astype(np.uint8)
    imageio.mimsave("renders/orbit.gif", imgs, "GIF", duration=0.05, loop=0)
    imageio.mimsave("renders/orbit_depth.gif", depth_imgs, "GIF", duration=0.05, loop=0)


# main
if __name__ == "__main__":
    load_path = f"logs\mk42_996_depth\mk42_996_depth_model.ply"
    render_orbit_imgs(load_path)
    grid_image = image_utils.resize_and_fit_images("renders", "renders/gird.png")
    render_gif(load_path)
