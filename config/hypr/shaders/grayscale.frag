#version 320 es

precision highp float;
in vec2 v_texcoord;
uniform sampler2D tex;

layout(location = 0) out vec4 fragColor;

void main() {
    vec4 pixColor = texture(tex, v_texcoord);
    float gray = pixColor.r * 0.299 + pixColor.g * 0.587 + pixColor.b * 0.114;
    fragColor = vec4(gray, gray, gray, pixColor.a);
}
