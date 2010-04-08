import math
from math import pi

import pyglet
from pyglet.window import key
from pyglet.gl import *

from shader import Shader as NewShader
import random

class ShaderWindow(pyglet.window.Window):

    sprite_files = ['eclipse.png', 'oval.png', 'bars.png', 'bevel.png', 'spiral.png', 'dots.png']
    num_keys = [key._0, key._1, key._2, key._3, key._4, key._5, key._6, key._7, key._8, key._9]
    angleinc = 0.00009

    def __init__(self, shader):
        # Create window
        super(ShaderWindow, self).__init__(1430, 890, caption="Shader Testing")
        # Setup mouse
        pyglet.resource.path.append('turntable')
        pyglet.resource.reindex()
        sprites = []
        for file in self.sprite_files:
            img = pyglet.resource.image(file)
            img.anchor_x = img.width / 2
            img.anchor_y = img.height / 2
            cur = pyglet.sprite.Sprite(img)
            cur.visible = False
            sprites.append(cur)
        self.cursors = sprites
        self.cursors[-1].visible = True
        self.cursorpos = [self.width/2.0, self.height/2.0]
        # Setup shader
        shader.bind()
        shader.uniformi('tex0', 0)
        shader.uniformi('tex1', 1)
        shader.unbind()
        self.shader = shader
        
        # Setup Texture
        texture = pyglet.image.Texture.create_for_size(GL_TEXTURE_RECTANGLE_ARB, self.width, self.height, internalformat=GL_RGBA)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.texture = texture
        # Create batch and quad
        batch = pyglet.graphics.Batch()
        batch.add(4, GL_QUADS, None, 
            ('v2i', (0, 0, self.width, 0, self.width, self.height, 0, self.height)), 
            ('t2f', (0, 0, self.width, 0, self.width, self.height, 0, self.height))
        )
        self.batch = batch
        
        self.setup_gl()
        #pyglet.clock.schedule(self.update)
        pyglet.clock.schedule_interval(self.update, 1.0/30.0)
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.pressed = False
        self.shading = False
        # set update function
        pyglet.clock.schedule_interval(self.update, 1.0/30.0)
        
        self.angledelta = 3.0
        self.angledir = 1.0
        self.angle = (2 * pi) / 3.0
        
        self.set_exclusive_mouse()
        
    def _get_cursor(self):
        return self.cursors[-1]
    cursor = property(_get_cursor)
        
    def update_cursor(self, dx, dy):
        self.cursorpos[0] += dx
        self.cursorpos[1] += dy
        self.cursorpos[0] = max(0.0, min(self.width, self.cursorpos[0]))
        self.cursorpos[1] = max(0.0, min(self.height, self.cursorpos[1]))
        self.cursor.x, self.cursor.y = self.cursorpos
        x, y = self.cursor.position        
        #self.angle = 3.141592653 / 0.4
        #self.angle = 45
        #self.angle = 0.14159265358979 / 0.38
        
        cdist = math.sqrt(((x - self.width/2.0)**2) + ((y - self.height/2.0)**2))
        rx = (self.width - self.height) / 2.0
        bx = self.width - rx
        gx = self.width / 2.0
        gy = self.height 
        rdist = 300 - math.sqrt(((x - rx)**2) + ((y - 0)**2)) / 2.0
        gdist = 300 - math.sqrt(((x - gx)**2) + ((y - gy)**2)) / 2.0
        bdist = 300 - math.sqrt(((x - bx)**2) + ((y - 0)**2)) / 2.0
        
        self.cursor.scale = max(0.1, cdist / 280)
        self.cursor.rotation = cdist
        
        rcomponent = max(20, min(255, rdist))
        gcomponent = max(20, min(255, gdist))
        bcomponent = max(20, min(255, bdist))
        self.cursor.color = (rcomponent, gcomponent, bcomponent)
        
    def next_cursor(self):
        spr = self.cursors.pop()
        spr.visible = False
        self.cursors.insert(0, spr)
        self.cursor.visible = True            

    def setup_gl(self):
        pyglet.gl.glClearColor(1.0, 0.0, 0.0, 1.0)
        pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
                pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
    def copyFramebuffer(self, tex, *size):
        # if we are given a new size
        if len(size) == 2:
            # resize the texture to match
            tex.width, tex.height = size[0], size[1]
        glBindTexture(tex.target, tex.id)
        glCopyTexImage2D(GL_TEXTURE_RECTANGLE_ARB, 0, GL_RGBA, 0, 0, tex.width, tex.height, 0);
        glBindTexture(tex.target, 0)
        
    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        # setup a simple 0-1 orthoganal projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        self.shader.bind()
        shader.uniformf('center', self.width/2.0, self.height/2.0)
        self.shader.unbind()
    
        # copy the framebuffer, which also resizes the texture
        self.copyFramebuffer(self.texture, width, height)

        return pyglet.event.EVENT_HANDLED
        
    def on_mouse_motion(self, x, y, dx, dy):
        self.update_cursor(dx, dy)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.pressed = True
        self.update_cursor(dx, dy)
        
    def on_mouse_release(self, x, y, buttons, modifiers):
        self.pressed = False
        
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.CAPSLOCK:
            self.shading = not self.shading
            return True
        elif symbol == pyglet.window.key.TAB:
            self.next_cursor()
        elif symbol in self.num_keys:
            self.angledelta = float(self.num_keys.index(symbol) + (self.angledelta % 1))
        elif symbol == pyglet.window.key.ESCAPE:
            self.on_close()
            
  
    def update(self, dt):
        self.angledelta += self.angleinc * self.angledir
        if self.angledelta >= 100.0:
            self.angledelta = 100.0
            self.angledir = -self.angledir
        elif self.angledelta <= 1.0:
            self.angledelta = 1.0
            self.angledir = -self.angledir
            
        print self.angledelta
            
        self.angle = (2 * pi) / self.angledelta
            

    def on_draw(self):
        glBindTexture(self.texture.target, self.texture.id)
        pyglet.gl.glClearColor(1.0, 0.0, 0.0, 1.0)
        self.clear()
        #glActiveTexture(GL_TEXTURE0 + 1)    
        #glBindTexture(texture1.target, texture1.id)
    
        
        if self.shading:
            self.shader.bind()
            shader.uniformf('angle', self.angle)
        self.batch.draw()
        if self.shading:
            self.shader.unbind()
        
        #self.bg.draw()
        if self.pressed:
            self.cursor.draw()

        #glBindTexture(self.texture.target, 0)
        #glBindTexture(texture1.target, 0)
    
        #glActiveTexture(GL_TEXTURE0)    
        
        # copy the result back into the texture
        self.copyFramebuffer(self.texture)

# create our shader
shader = NewShader(['''
void main() {
    // transform the vertex position
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    // pass through the texture coordinate
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
'''], ['''
uniform sampler2DRect tex0;
uniform float angle;
uniform vec2 center;

void main() {
    //vec2 center = vec2(400.0);
    
    // retrieve the texture coordinate
    vec2 c = gl_TexCoord[0].xy - center;
    
    float x = c.x * cos(angle) - c.y * sin(angle);
    float y = c.x * sin(angle) + c.y * cos(angle);
    
    c = vec2(x, y) + center;

    vec3 newcolor = texture2DRect(tex0, c).rgb ;

    // write out the pixel
    gl_FragColor = vec4(newcolor, 1.0);
}
'''])


def run():
    global shader
    window = ShaderWindow(shader)
    pyglet.app.run()
    
if "__main__" == __name__:
    run()
