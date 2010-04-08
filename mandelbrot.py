import math
from math import pi

import pyglet
from pyglet.window import key
from pyglet.gl import *

from shader import Shader as NewShader
import random

class ShaderWindow(pyglet.window.Window):
    wanderdistance = .5
    max_iters = 400.0
    min_iters = 16.0
    max_zoom = 3.03439295521e-05
    def __init__(self, shader):
        # Create window
        super(ShaderWindow, self).__init__(800, 800, caption="Shader Testing")
        # Setup mouse

        shader.bind()
        
        shader.uniformf('MaxIterations', 50.0)
        shader.uniformf('Zoom', 1.0)
        shader.uniformf('Xcenter', 0.0)
        shader.uniformf('Ycenter', 0.0)
        
        shader.uniformf('InnerColor', 0.0, 0.0, 0.0)
        shader.uniformf('OuterColor2', 1, 1, 1)
        shader.uniformf('OuterColor1', 1.0, 1.0, 1.0)
        shader.unbind()
        self.shader = shader
        self.center = [0, 0]
        self.zoom = 1.0
        self.zoomdir = 1.0
        self.zoomspeed = .45
        
        self.quality_timeout = .05
        self.quality_time = 0.0
        self.quality_delta = 1.0
        self.quality = 400
        
        self.dodraw = 2
        
        self.color = (1.0, 1.0, 1.0)
        
        self.xwander = 0.0
        self.ywander = 0.0
        self.xspeed = .1
        self.yspeed = .1
        self.xdir = 1.0
        self.ydir = 1.0
        self.xdist = random.randint(-5, 5)/10.0
        # Setup Texture
        texture = pyglet.image.Texture.create_for_size(GL_TEXTURE_RECTANGLE_ARB, self.width, self.height, internalformat=GL_RGBA)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.texture = texture
        # Create batch and quad
        batch = pyglet.graphics.Batch()
        batch.add(4, GL_QUADS, None, 
            ('v2i', (0, 0, self.width, 0, self.width, self.height, 0, self.height)), 
            ('t2f', (0, 0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0))
        )
        self.batch = batch
        
        self.setup_gl()
        
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        # set update function
        pyglet.clock.schedule_interval(self.update, 1.0/30.0)
        


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
        
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.dodraw = 2
        self.zoom = min(1.0, max(self.max_zoom, self.zoom + (scroll_y * (-0.02 * self.zoom))))
        self.quality_time += self.quality_timeout
        self.quality_time = min(.5, self.quality_time)
        
        #self.on_mouse_press(x, y, pyglet.window.mouse.LEFT, None)
    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        # setup a simple 0-1 orthoganal projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        self.shader.bind()
        self.shader.unbind()
    
        # copy the framebuffer, which also resizes the texture
        self.copyFramebuffer(self.texture, width, height)
        return pyglet.event.EVENT_HANDLED
        
    def on_mouse_motion(self, x, y, dx, dy):
        rdist = math.sqrt(((x - 0)**2) + ((y - 0)**2)) / 2.0
        gdist = math.sqrt(((x - self.width/2.0)**2) + ((y - self.height)**2)) / 2.0
        bdist = math.sqrt(((x - self.width)**2) + ((y - 0)**2)) / 2.0
        
        r = 1 - max(1, rdist * 0.9) / 255
        g = 1 - max(1, gdist * 0.9) / 255
        b = 1 - max(1, bdist * 0.9) / 255
        
        self.color = (r, g, b)
        self.quality_time += self.quality_timeout
        self.quality_time = min(.5, self.quality_time)
        self.dodraw = 2
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass
        
    def on_mouse_press(self, x, y, buttons, modifiers):
        self.dodraw = 2
        if buttons == pyglet.window.mouse.LEFT:
            dx = 5*((x - self.width/2.0)/self.width)
            dy = 5*((y - self.height/2.0)/self.height)
            self.center[0] += dx * self.zoom
            self.center[1] += dy * self.zoom
        self.zoom *= 0.92
        
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
            
  
    def update(self, dt):
        old = self.quality_time
        self.quality_time = max(0.0, self.quality_time - (self.quality_delta * dt))
        if not self.quality_time and old:
            self.dodraw = 2
        
        #=======================================================================
        # self.zoom += self.zoomspeed * (self.zoom * 2) * dt * self.zoomdir
        # if self.zoom <= self.max_zoom or self.zoom >= 1.0:
        #    self.zoomdir = -self.zoomdir
        #    self.zoom = min(1.0, max(self.max_zoom, self.zoom))
        # self.center[0] += self.xspeed * dt * self.xdir * self.zoom
        # self.xwander += self.xspeed * dt * self.xdir * self.zoom 
        # if self.xwander >= self.xdist or self.xwander <= 0.0:
        #    self.xdir = -self.xdir
        #    self.xwander = min(self.xdist, max(0.0, self.xwander))  
        #    self.xdist = random.randint(-10, 10)/100.0 
        #=======================================================================
            

    def on_draw(self):
        if self.dodraw > 0:
            self.clear()
            self.dodraw -= 1
            glBindTexture(self.texture.target, self.texture.id)
            pyglet.gl.glClearColor(1.0, 0.0, 0.0, 1.0)
            #glActiveTexture(GL_TEXTURE0 + 1)    
            #glBindTexture(texture1.target, texture1.id)
        
            
            self.shader.bind()
            shader.uniformf('Xcenter', self.center[0])
            shader.uniformf('Ycenter', self.center[1])
            shader.uniformf('Zoom', self.zoom)
            iters = self.max_iters * (1.0 - (self.zoom ** .02))
            iters = 400.0 if not self.quality_time else max(self.min_iters, iters)
            #print self.zoom, iters
            shader.uniformf('MaxIterations', iters)
            shader.uniformf('OuterColor1', *self.color)
            self.batch.draw()
            self.shader.unbind()
            
    
            #glBindTexture(self.texture.target, 0)
            #glBindTexture(texture1.target, 0)
        
            #glActiveTexture(GL_TEXTURE0)    
            
            # copy the result back into the texture
        self.copyFramebuffer(self.texture)

# create our shader
shader = NewShader(['''
varying vec3  Position;

void main()
{
    Position        = vec3(gl_MultiTexCoord0 - 0.5) * 5.0;
    gl_Position     = ftransform();
}
'''], ['''
varying vec3  Position;

uniform float MaxIterations;
uniform float Zoom;
uniform float Xcenter;
uniform float Ycenter;
uniform vec3  InnerColor;
uniform vec3  OuterColor1;
uniform vec3  OuterColor2;

void main()
{
    float   real  = Position.x * Zoom + Xcenter;
    float   imag  = Position.y * Zoom + Ycenter;
    float   Creal = real;   // Change this line. . .
    float   Cimag = imag;   // . . .and this one to get a Julia set

    float r2 = 0.0;
    float iter;

    for (iter = 0.0; iter < MaxIterations && r2 < 4.0; ++iter)
    {
        float tempreal = real;

        real = (tempreal * tempreal) - (imag * imag) + Creal;
        imag = 2.0 * tempreal * imag + Cimag;
        r2   = (real * real) + (imag * imag);
    }

    // Base the color on the number of iterations

    vec3 color;

    if (r2 < 4.0)
        color = InnerColor;
    else
        color = mix(OuterColor1, OuterColor2, fract(iter * 0.05));

    gl_FragColor = vec4(color, 1.0);
}
'''])


def run():
    global shader
    window = ShaderWindow(shader)
    pyglet.app.run()
    
if "__main__" == __name__:
    run()
