# Inspired by work by Tristam Macdonald.

# TODO:
# - //= main and //= main-end can probably be parsed from source itself.
# - Better error checking during preprocessing.
# - Automatic fallback / shutoff of unsupported things.

"""Programmable shader (GLSL) support for Layer.

Layer GLSL consists of a valid GLSL program with small source comment
annotations in order to parse, decompose, concatenate, and recompose
different shaders.

An example program (which tints things red):

    //= preamble
    uniform sampler2D tex0;

    //= body
    uniform vec4 tint = vec4(1.0, 0.0, 0.0, 1.0);

    //= main
    void main(void) {
        //= main-preamble
        vec4 color = gl_Color * texture2D(tex0, gl_TexCoord[0].xy);

        //= main-body
        color *= tint;

        //= main-postscript
        gl_FragColor = color;

        //= main-end
    }

"""

import weakref

# Use Layer features if available, otherwise use normal Python and
# pyglet.
try:
    from layer.gl import *
except ImportError:
    from pyglet.gl import *

__all__ = ["ShaderProgram", "ShaderSource"]

# Stub out some functions Layer expects to be able to use.
try:
    print_d
except NameError:
    def print_d(text, *args, **kwargs):
        print text
try:
    print_e
except NameError:
    print_e = print_d

c_pp_char = POINTER(POINTER(c_char))
    
class ShaderSource(object):
    """Source for an individual GLSL fragment or vertex shader.

    The source is split into several parts, which allows source-level
    transforms (most importantly, concatenation) while still
    maintaining correct syntax.

    The parts are marked in the GLSL code via use of the following
    comments:

    //= preamble
    //= body
    //= main
    //= main-preamble
    //= main-body
    //= main-postscript
    //= main-end

    The intention is that program annotated in this style is still a
    valid GLSL shader program by itself, but can also be combined with
    other shaders with minimal parsing effort. When constructing a
    shader from multiple sources, the following rules are used:

    * Duplicate lines are removed from the preamble, preserving the
      order (so the second and onward are removed). This allows safe
      multiple declarations of variables common to all shaders, e.g.
          uniform sampler2D tex0;

    * The body blocks are concatenated with no further processing.

    * The code between the main and main_preamble blocks is discarded
      and replaced with a generic "void main(void) {" stanza.

    * The main-preamble block, like the preamble block, has duplicate
      lines removed. This may be used to initialize common variables,
      e.g.
          vec4 color = texture2D(tex0, gl_TexCoord[0].xy) * gl_Color;

    * The main-body blocks are concatenated.

    * The main-postscript block likewise has duplicate lines
      removed. The intended use is to finish setting relevant out
      variables, e.g.
          gl_FragColor = color;

    * Everything from main-end to the end of the file is replaced with
      "}".

    """

    __slots__ = ["preamble", "body",
                 "main_preamble", "main_body", "main_postscript"]

    def __init__(self, source="", preamble="", body="",
                 main_preamble="", main_body="", main_postscript=""):
        """Create a preprocessed shader source.

        This can be done via a whole source string, or specifying each
        part individually.
        """
        self.preamble = preamble
        self.body = body
        self.main_preamble = main_preamble
        self.main_body = main_body
        self.main_postscript = main_postscript
        if source.strip():
            self._parse(source)

    def _parse(self, source):
        dont_include = ["main", "main-end"]
        sections = ["preamble", "body", "main", "main-preamble",
                    "main-body", "main-postscript", "main-end"]
        while sections:
            section = sections.pop(0)
            if section in dont_include:
                continue
            try:
                start = source.index("//= " + section + "\n")
            except ValueError:
                continue
            else:
                while sections:
                    next_section = sections[0]
                    try:
                        end = source.index("//= " + next_section + "\n")
                    except ValueError:
                        sections.pop(0)
                    else:
                        text = source[start:end]
                        text = text[text.index("\n") + 1:]
                        setattr(self, section.replace("-", "_"), text)
                        break

    def __add__(self, other):
        """Combine two shaders programs via source-level transforms."""

        preamble = self.preamble.splitlines()
        stripped = [line.strip() for line in preamble]
        for line in other.preamble.splitlines():
            if line.strip() not in stripped:
                preamble.append(line)
        if preamble:
            preamble.append("")

        main_preamble = self.main_preamble.splitlines()
        stripped = [line.strip() for line in main_preamble]
        for line in other.main_preamble.splitlines():
            if line.strip() not in stripped:
                main_preamble.append(line)

        main_postscript = self.main_postscript.splitlines()
        stripped = [line.strip() for line in main_postscript]
        for line in other.main_postscript.splitlines():
            if line.strip() not in stripped:
                main_postscript.append(line)

        if self.body and other.body:
            body = self.body + "\n" +other.body
        elif self.body:
            body = self.body
        else:
            body = other.body

        if self.main_body and other.main_body:
            main_body = self.main_body + "\n" + other.main_body
        elif self.main_body:
            main_body = self.main_body
        else:
            main_body = other.main_body

        return ShaderSource(
            preamble="\n".join(preamble),
            body=body,
            main_preamble="\n".join(main_preamble),
            main_body=main_body,
            main_postscript="\n".join(main_postscript))

    def source(self):
        return "".join([(self.preamble and "//= preamble\n" + self.preamble),
                        (self.body and "//= body\n" + self.body),
                        (self.main_preamble or self.main_body
                         or self.main_postscript)
                        and "//= main\nvoid main(void) {\n\t",
                        (self.main_preamble and
                         "//= main-preamble\n" + self.main_preamble),
                        (self.main_body and
                         "//= main-body\n" + self.main_body),
                        (self.main_postscript and
                         "//= main-postscript\n" + self.main_postscript),
                        (self.main_preamble or self.main_body
                         or self.main_postscript) and
                        "//= main-end\n}\n"
                        ])
    source = property(source,
                      doc="Source string for this shader.")

    try:
        from layer.load import (file as _Open,
                                ResourceNotFoundException as _Expected)
    except ImportError:
        try:
            from pyglet.resource import (file as _Open,
                                         ResourceNotFoundException as _Expected)
        except ImportError:
            _Open = file
            _Expected = EnvironmentError

    @staticmethod
    def _Open(filename, Open=_Open, Expected=_Expected):
        """Open a shader file and parse the data.

        If the file cannot be found, a "do-nothing" shader is returned.
        """
        try:
            return ShaderSource(Open(filename).read())
        except Expected:
            return ShaderSource()
        except Exception, err:
            print_d(str(err))
            return ShaderSource()
    
class ShaderProgram(object):
    """Compiled shader program that can be bound to the GPU and used."""
    
    _Active = []
    _Programs = weakref.WeakKeyDictionary()
    _Sources = {}

    __slots__ = ["_handle", "_sources", "_rebuild", "_shaders", "_locations",
                 "__weakref__"]

    def __init__(self, *sources):
        """Create a shader program based on some source files.

        Each name is a filename to look up (using Layer, pyglet, or
        the native filesystem, depending on what's available). Vertex
        shaders are loaded using <name>.vert, and fragment shaders
        using <name>.frag.

        The shader file format is described in the docstrings for
        ShaderSource.

        Virtually no errors are raised by default. If none of the
        shader names given are found, a no-op program is created. If
        some are not found, they are simply ignored. If compilation
        fails, behavior is OpenGL-implementation-dependent.
        """

        self._handle = glCreateProgram()
        self._Programs[self] = None
        self._shaders = set()
        self._locations = {}
        self._sources = sources
        self._build()

    def _build(self):
        """Compile and link a shader program based on its definitions."""
        for shader in self._shaders:
            glDetachShader(self._handle, shader)
            glDeleteShader(shader)
        self._shaders.clear()
        self._locations.clear()

        vertex = ShaderSource()
        fragment = ShaderSource()
        for source in self._sources:
            if source not in self._Sources:
                self._Sources[source] = (ShaderSource._Open(source + ".vert"),
                                         ShaderSource._Open(source + ".frag"))
            vertex += self._Sources[source][0]
            fragment += self._Sources[source][1]
            
        for (source, type) in [(vertex.source, GL_VERTEX_SHADER),
                               (fragment.source, GL_FRAGMENT_SHADER)]:
            shader = self._compile(source, type)
            if shader is not None:
                self._shaders.add(shader)

        self._link()
        self._rebuild = False

    def _compile(self, source, type):
        """Compile this program.

        'shader' should be the result of a previous call to this
        method.
        """
        if not (source and source.strip()):
            return None
        else:
            strings = [source]

        print_d("Creating shader %r." % type, context=self)
        shader = glCreateShader(type)

        count = len(strings)
        src = (c_char_p * count)(*strings)
        glShaderSource(shader, count, cast(pointer(src), c_pp_char), None)

        glCompileShader(shader)

        temp = c_int(0)
        glGetShaderiv(shader, GL_COMPILE_STATUS, byref(temp))

        if not temp:
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(temp))
            buffer = create_string_buffer(temp.value)
            glGetShaderInfoLog(shader, temp, None, buffer)
            print_e(buffer.value)
            glDeleteShader(shader)
            return None
        else:
            print_d("Attaching shader %r." % type, context=self)
            glAttachShader(self._handle, shader);
            return shader

    def _link(self):
        """Link this program."""
        print_d("Linking shader %r." % self, context=self)
        glLinkProgram(self._handle)

        temp = c_int(0)
        glGetProgramiv(self._handle, GL_LINK_STATUS, byref(temp))

        if not temp:
            glGetProgramiv(self._handle, GL_INFO_LOG_LENGTH, byref(temp))
            buffer = create_string_buffer(temp.value)
            glGetProgramInfoLog(self._handle, temp, None, buffer)
            print_e(buffer.value)
        return bool(temp)

    def bind(self):
        """Make this shader program active.

        Programs (but not their effects) are maintained in a stack, so:
            A.bind()
            B.bind()
            B.unbind()

        Will leave A active.
        """
        if self._rebuild:
            self._build()
        if not (self._Active and self._Active[-1] is self):
            glUseProgram(self._handle)
        self._Active.append(self)

    def unbind(self):
        """If this shader program is active, stop using it.

        No effect takes place if this is not the active program, e.g.

            A.bind()
            B.bind()
            A.unbind() # B is still active after this.
            B.unbind() # A is still active after this.

        An unbind must be called for each bind:

           A.bind()
           B.bind()
           B.bind()   # Safe, but...
           B.unbind() # B is still active after this.
           B.unbind() # A is now active again after this.
        """
        if self._Active[-1] is self:
            self._Active.pop()
            if self._Active:
                if self._Active[-1] is not self:
                    glUseProgram(self._Active[-1]._handle)
            else:
                glUseProgram(0)

    def __enter__(self):
        """Bind a program for the duration of a `with` context.
        
        Setting uniforms in an unbound program will be slow, because
        the shader will get bound, set, and unbound for each uniform.
        ShaderPrograms support the Python with statement to batch
        uniform setter calls:
            with program:
                program.uniform('color', color)
                program.uniform('light', light)
                ...

        This is not necessary if you have bound the program yourself
        (e.g. you intend to actually render something with it).
        """
        self.bind()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.unbind()

    def location(self, name):
        """Get a uniform location."""
        try:
            return self._locations[name]
        except KeyError:
            self._locations[name] = glGetUniformLocation(self._handle, name)
            return self._locations[name]

    def uniformf(self, name, *vals):
        """Upload a uniform floating point value."""
        with self:
            [glUniform1f, glUniform2f, glUniform3f, glUniform4f
             ][len(vals) - 1](self.location(name), *vals)

    def uniformi(self, name, *vals):
        """Upload a uniform integer value."""
        with self:
            [glUniform1i, glUniform2i, glUniform3i, glUniform4i
             ][len(vals) - 1](self.location(name), *vals)

    def uniform_matrixf(self, name, mat):
        """Upload a uniform matrix value."""
        with self:
            glUniformMatrix4fv(
                self.location(name), 1, False, (c_float * 16)(*mat))

    def uniform(self, name, *vals):
        """Upload a uniform value.

        The type is automatically detected.
        """
        if isinstance(vals[0], int):
            self.uniformi(name, *vals)
        elif isinstance(vals[0], float):
            self.uniformf(name, *vals)
        else:
            self.uniform_matrixf(name, *vals)

    def __add__(self, other):
        """Concatenate two programs at the source level."""
        return type(self)(*(self._sources + other.sources))

    def __del__(self):
        """Programs and shaders are deleted when no references exist."""
        for shader in self._shaders:
            glDetachShader(self._handle, shader)
            glDeleteShader(shader)
        glDeleteProgram(self._handle)


    @classmethod
    def UnbindAll(cls):
        """Stop using all shader programs."""
        glUseProgram(0)
        del(cls._Active[:])

    @classmethod
    def _Reload(cls, name):
        name = name.lower().rsplit(".", 1)[0]
        name = name.split("/")[-1]
        name = name.split("\\")[-1]
        try: del(cls._Sources[name])
        except KeyError: pass
        for program in cls._Programs:
            if name.lower() in program._sources:
                program._rebuild = True

try:
    import layer.reload
except ImportError:
    pass
else:
    layer.reload.register("*.vert", ShaderProgram._Reload)
    layer.reload.register("*.frag", ShaderProgram._Reload)
