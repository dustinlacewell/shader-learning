import pyglet
from pyglet.window import key
from pyglet.gl import *

from shader import Shader

class ShaderWindow(pyglet.window.Window):
    def __init__(self, shader):
        # Create window
        super(ShaderWindow, self).__init__(640, 640, caption="Shader Testing")
        # Shader constants
        shader.bind()
        shader.uniformi('tex0', 0)
        shader.uniformf('pixel', 1.0/self.width, 1.0/self.height)
        shader.unbind()
        self.shader = shader
        # Setup Texture
        texture = pyglet.image.Texture.create_for_size(GL_TEXTURE_RECTANGLE_ARB, self.width, self.height, internalformat=GL_RGBA)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.texture = texture
        # Create fullscreen quad (batch)
        batch = pyglet.graphics.Batch()
        batch.add(4, GL_QUADS, None, 
            ('v2i', (0, 0, self.width, 0, self.width, self.height, 0, self.height)), 
            ('t2f', (0, 0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0))
        )
        self.batch = batch
        # General GL Setup
        self.setup_gl()
        # Key tracking
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        # Set update function
        pyglet.clock.schedule_interval(self.update, 1.0/30.0)
        

    def setup_gl(self):
        pyglet.gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
                pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
    def copyFramebuffer(self, tex, *size):
        """Copy framebuffer into texture."""
        if len(size) == 2: # resize the texture to match if new size is provided
            tex.width, tex.height = size[0], size[1]
        glBindTexture(tex.target, tex.id)
        glCopyTexImage2D(GL_TEXTURE_RECTANGLE_ARB, 0, GL_RGBA, 0, 0, tex.width, tex.height, 0);
        glBindTexture(tex.target, 0)
        
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass
        
        #self.on_mouse_press(x, y, pyglet.window.mouse.LEFT, None)
    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        # setup a simple 0-1 orthoganal projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        self.shader.bind()
        shader.uniformf('pixel', 1.0/width, 1.0/height)
        self.shader.unbind()
    
        # copy the framebuffer, which also resizes the texture
        self.copyFramebuffer(self.texture, width, height)
        return pyglet.event.EVENT_HANDLED
        
    def on_mouse_motion(self, x, y, dx, dy):
        pass
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass
        
    def on_mouse_press(self, x, y, buttons, modifiers):
        pass
        
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
            
  
    def update(self, dt):
        pass            

    def on_draw(self):
        self.clear()
        glBindTexture(self.texture.target, self.texture.id)
        #glActiveTexture(GL_TEXTURE0 + 1)    
        #glBindTexture(texture1.target, texture1.id)
    
        
        self.shader.bind()
        
        #shader.uniformf('value', 1.0)
        
        self.batch.draw()
        
        self.shader.unbind()
        glBindTexture(self.texture.target, 0)
        
        # copy the result back into the texture
        self.copyFramebuffer(self.texture)

# create our shader
shader = Shader(['''
varying vec3  Position;

void main()
{
    // transform the vertex position
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    // pass through the texture coordinate
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
'''], ['''
uniform sampler2DRect tex0;
uniform vec2 pixel;

void main() {
    vec2 pos = gl_TexCoord[0].xy;
    vec2 rpos = pos / pixel;

    gl_FragColor = (mod(rpos.x, 5.0) <= 1.0 || mod(rpos.y, 5.0) <= 1.0) ? vec4(1.0) : vec4(0.0);
}
'''])


def run():
    global shader
    window = ShaderWindow(shader)
    pyglet.app.run()
    
if "__main__" == __name__:
    run()
