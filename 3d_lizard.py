from ursina import *
import math
import random

app = Ursina()
window.title = "Lizard Waving Inside a Transparent Sphere"

SPHERE_RADIUS = 6
LIZARD_SIZE = 1.0
SPINE_LEN = 13
SPINE_SPACING = 0.35 * LIZARD_SIZE
LIMB_LEN = 1.25 * LIZARD_SIZE

# Make the transparent sphere
planet = Entity(model='sphere', color=color.azure.tint(-.1), scale=SPHERE_RADIUS*2, y=0,
                double_sided=True, alpha=0.23)

# Shadow at the bottom of the sphere
shadow = Entity(model='circle', color=color.black33, scale=(1.6*LIZARD_SIZE,1.6*LIZARD_SIZE,1), y=-SPHERE_RADIUS+0.18, z=0)

# Lizard's floating center point
center = Vec3(0, 0, 0)

# Build lizard bones
spine_bones = [Entity(model='sphere', color=color.white, scale=(0.25*LIZARD_SIZE, 0.27*LIZARD_SIZE, 0.25*LIZARD_SIZE)) for _ in range(SPINE_LEN)]
head = Entity(model='sphere', color=color.azure, scale=(0.44*LIZARD_SIZE, 0.38*LIZARD_SIZE, 0.54*LIZARD_SIZE))
eyes = [Entity(model='sphere', color=color.black, scale=(0.09*LIZARD_SIZE,0.12*LIZARD_SIZE,0.12*LIZARD_SIZE)) for _ in range(2)]
limbs = [[],[]]
for _ in range(2):
    limbs[0].append([Entity(model='cylinder', color=color.brown.tint(-0.15), scale=(0.09*LIZARD_SIZE, LIMB_LEN*LIZARD_SIZE, 0.09*LIZARD_SIZE)),
                     Entity(model='cylinder', color=color.white, scale=(0.06*LIZARD_SIZE, LIMB_LEN*0.7*LIZARD_SIZE, 0.06*LIZARD_SIZE))])
    limbs[1].append([Entity(model='cylinder', color=color.brown.tint(-0.05), scale=(0.11*LIZARD_SIZE, LIMB_LEN*1.12*LIZARD_SIZE, 0.11*LIZARD_SIZE)),
                     Entity(model='cylinder', color=color.white, scale=(0.07*LIZARD_SIZE, LIMB_LEN*0.72*LIZARD_SIZE, 0.07*LIZARD_SIZE))])

toes = []
for li in range(4):
    tlist = []
    for t in range(-2,3):
        e = Entity(model='cylinder', color=color.white66, scale=(0.03*LIZARD_SIZE, 0.28*LIZARD_SIZE, 0.03*LIZARD_SIZE))
        tlist.append(e)
    toes.append(tlist)

# Camera movement variables
orbit_angle = 0
orbit_radius = SPHERE_RADIUS * 0.6

def update():
    t = time.time()
    global orbit_angle

    # Lizard's center floats in a 3D circle (inside sphere)
    orbit_angle += time.dt * 0.26
    center.x = math.sin(orbit_angle*0.7) * orbit_radius * 0.45
    center.y = math.sin(orbit_angle*0.32) * orbit_radius * 0.39
    center.z = math.cos(orbit_angle*0.44) * orbit_radius * 0.47

    # Animate spine in a "snake wave" inside the sphere
    dir_angle = orbit_angle
    for i, bone in enumerate(spine_bones):
        f = i/(SPINE_LEN-1)
        ang = dir_angle + math.sin(t*1.4 + i*0.6) * 0.25 * (1-f)
        bone.x = center.x + math.sin(ang) * (0.5 + i*SPINE_SPACING*0.72)
        bone.y = center.y + math.sin(ang*1.2 + i*0.35) * (0.18 + i*SPINE_SPACING*0.68)
        bone.z = center.z + math.cos(ang*0.96 + i*0.34) * (0.6 + i*SPINE_SPACING*0.89)
        # Look toward next bone
        if i < SPINE_LEN-1:
            bone.look_at(Vec3(spine_bones[i+1].x, spine_bones[i+1].y, spine_bones[i+1].z))
        else:
            bone.look_at(bone.position + Vec3(1,0,0))

    # Head at the front
    head.position = spine_bones[0].position + head.forward*0.04
    head.look_at(spine_bones[1].position)
    # Eyes
    fwd = (spine_bones[1].position - head.position).normalized()
    right = Vec3.cross(fwd, Vec3(0,1,0)).normalized()
    up = Vec3.cross(right, fwd).normalized()
    eyes[0].position = head.position + right*0.19 + up*0.10 + fwd*0.18
    eyes[1].position = head.position - right*0.19 + up*0.10 + fwd*0.18

    # Limbs: arms (front) and legs (back) with proper orientation
    arm_bone = spine_bones[3]
    leg_bone = spine_bones[-4]
    for idx, (parent, upper, lower, is_leg) in enumerate([
        (arm_bone, limbs[0][0][0], limbs[0][0][1], False),
        (arm_bone, limbs[0][1][0], limbs[0][1][1], False),
        (leg_bone, limbs[1][0][0], limbs[1][0][1], True),
        (leg_bone, limbs[1][1][0], limbs[1][1][1], True),
    ]):
        # Find normal vector (cross product)
        if not is_leg:
            base_idx = 3
        else:
            base_idx = SPINE_LEN-4
        if 1 <= base_idx < SPINE_LEN-1:
            tangent = (spine_bones[base_idx+1].position - spine_bones[base_idx-1].position).normalized()
        else:
            tangent = Vec3(1,0,0)
        up_vec = (spine_bones[base_idx].position - Vec3(0,0,0)).normalized()
        normal = up_vec.cross(tangent).normalized()
        side = -1 if idx%2==0 else 1
        normal = normal * side
        # Animate "walking" limbs:
        walk_phase = t*2 + idx*math.pi
        limb_angle = 0.55 + math.sin(walk_phase)*0.47
        # Upper limb
        upper.position = parent.position + normal*0.33*LIZARD_SIZE
        upper.look_at(parent.position + normal*0.95*LIZARD_SIZE + tangent*limb_angle*0.44)
        # Lower limb (jointed)
        lower.position = upper.position + upper.forward * (LIMB_LEN*0.52*LIZARD_SIZE if is_leg else LIMB_LEN*0.41*LIZARD_SIZE)
        lower.look_at(upper.position + upper.forward * 1 + tangent*limb_angle*0.34)
        # Toes (fan out)
        toe_root = lower.position + lower.forward*0.66*LIZARD_SIZE
        for t2, toe in enumerate(toes[idx]):
            ang = (t2-2)*0.23
            toe.position = toe_root + lower.right*math.sin(ang)*0.19*LIZARD_SIZE + lower.up*math.cos(ang)*0.06*LIZARD_SIZE
            toe.look_at(toe.position + lower.forward)

    # Shadow at bottom (y = -radius)
    shadow.position = Vec3(center.x, -SPHERE_RADIUS+0.18, center.z)
    shadow.look_at(Vec3(center.x,0,center.z))

EditorCamera()
app.run()

