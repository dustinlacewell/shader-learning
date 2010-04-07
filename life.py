import pyglet
from pyglet.window import key
from pyglet.gl import *

from shader import Shader as NewShader
import random

class ShaderWindow(pyglet.window.Window):
    def __init__(self, shader):
        # Create window
        super(ShaderWindow, self).__init__(800, 800, caption="Shader Testing")
        # Setup Background
        img = pyglet.image.load("bg.png")
        img.anchor_x = img.width / 2
        img.anchor_y = img.height / 2
        self.bg = pyglet.sprite.Sprite(img)
        self.bg.x = 300
        self.bg.y = 30
        # Setup mouse
        img = pyglet.image.load('cursor.png')
        img.anchor_x = img.width / 2
        img.anchor_y = img.height / 2
        cur = pyglet.sprite.Sprite(img)
        self.cur = cur
        # Setup shader
        shader.bind()
        shader.uniformi('tex0', 0)
        shader.uniformi('tex1', 1)
        shader.unbind()
        self.shader = shader
        # Setup Texture
        texture = pyglet.image.Texture.create_for_size(GL_TEXTURE_RECTANGLE_ARB, self.bg.width, self.bg.height, internalformat=GL_RGBA)
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
        # set update function
        pyglet.clock.schedule(self.update)
        
        self.angle = 1.0
        
    def on_mouse_motion(self, x, y, dx, dy):
        self.cur.x = x
        self.cur.y = y
        
        self.angle = max(1.0, abs(dx) / 10.0)
            

    def setup_gl(self):
        pyglet.gl.glClearColor(1.0, 1.0, 1.0, 1.0)
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
    
        # copy the framebuffer, which also resizes the texture
        self.copyFramebuffer(self.texture, width, height)

        return pyglet.event.EVENT_HANDLED
  
    def update(self, dt):
        pass

    def on_draw(self):
        self.clear()
        
    
        glBindTexture(self.texture.target, self.texture.id)
        #glActiveTexture(GL_TEXTURE0 + 1)    
        #glBindTexture(texture1.target, texture1.id)
    
        
        if self.keys[key.SPACE]:
            self.shader.bind()
            shader.uniformf('angle', self.angle)
        self.batch.draw()
        if self.keys[key.SPACE]:
            self.shader.unbind()
        
        #self.bg.draw()
        self.cur.draw()

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

void main() {
    vec2 center = vec2(400.0);
    
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
