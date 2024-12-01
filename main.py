import socket
import ssl
import tkinter
import tkinter.font

FONTS = {}
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
LINE_BREAKS = 25


class Text:
    def __init__(self, text):
        self.text = text


class Tag:
    def __init__(self, tag):
        self.tag = tag


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.case = 'lower'
        self.align = "left"
        self.subscript = False
        for tok in tokens:
            self.token(tok)
        self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            if(self.align=='center'):
                line_width = sum(font.measure(word) + font.measure(" ") for _, word, font in self.line)
                x = (WIDTH - line_width) // 2
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        # if(self.subscript):
        #     self.cursor_y = baseline - 3 * max_descent
        # else:
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []
        print("curosr in flush {}".format(self.cursor_y))

        # Function to create display entries with correct x,y and font

    def word(self, word):
        if (self.case == 'upper'):
            word = word.upper();
        if(self.subscript):
            self.cursor_y -= VSTEP/2
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if word == r'\n':
            self.cursor_y += LINE_BREAKS * 100
        # print(self.cursor_y)
        if self.cursor_x + w >= WIDTH - HSTEP:
            self.flush()
            # self.cursor_y += font.metrics("linespace") * 1.25
            # self.cursor_x = HSTEP
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

    # Function to idenfiy the token and set the word function
    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4

        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "abbr":
            self.weight = "bold"
            self.case = "upper"
        elif tok.tag == "/abbr":
            self.weight = "normal"
            self.case = "lower"
        elif tok.tag.startswith("h1") and 'class="title"' in tok.tag:
            self.align = 'center'
            self.size = 24  # Optional: Set a larger font size for title
            self.weight = "bold"
        elif tok.tag == "/h1":
            self.align = 'left'
            self.size = 12  # Reset size
            self.weight = "normal"
            self.flush()
        elif tok.tag == "sup":
            self.size = self.size // 2
            self.subscript = True
        elif tok.tag == "/sup":
            self.size = self.size * 2
            self.subscript = False
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP



class Browser:
    def __init__(self):
        self.y = 0
        self.x = 0
        self.scroll = 0
        self.window = tkinter.Tk()
        self.bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )
        self.window.bind("<MouseWheel>", self.scrolldown)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(fill="both", expand=1, )

    # Function to scroll down
    def scrolldown(self, e):
        if self.scroll - e.delta >= 0:
            self.scroll -= e.delta
        self.draw()

    # Function to load the output as per the request
    def load(self, url, direction='left'):
        tokens = []
        try:
            print("inside if of load")
            if url.type == "file":
                finalPath = url.filepath.replace("\\", "\\\\")
                f = open(finalPath)
                tokens.append(Text(f.read()))

            elif url.type == "data":
                tokens = lex(url.html)
            else:
                body = url.request()
                tokens = lex(body)
        except:

            print("inside except")
            text = "about:blank"
        if (direction == 'right'):
            self.display_list = layout_reverse(text)
        else:
            self.display_list = Layout(tokens).display_list
        self.draw()

    # Function to actually draw the letters on the canvas
    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            # print("y is {}".format(y))
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            # print(y);
            self.canvas.create_text(x, y - self.scroll, text=c, anchor='nw', font=font)


class Url:
    # Formatting request URL to find the HTTP Version,host and path
    def __init__(self, url):
        try:
            self.type, self.content = url.split(":", 1)
            assert self.type in ["http", "https", "file", "data", "view-source", "about"]
            self.data = ""
            if self.type == 'data':
                self.data, self.html = self.content.split(",")
            elif self.type == 'file':
                self.type, self.filepath = url.split("://")

            else:
                if self.type in "view-source":
                    self.scheme, url = self.content.split("://", 1)
                else:
                    self.scheme, url = url.split("://", 1)
                if self.scheme in ["http", "https"]:
                    if "/" not in url:
                        url = url + "/"
                    self.host, url = url.split("/", 1)
                    self.path = "/" + url
                    if self.scheme == "http":
                        self.port = 80
                    elif self.scheme == "https":
                        self.port = 443
                    if ":" in self.host:
                        self.host, port = self.host.split(":", 1)
                        self.port = int(port)
                    if self.scheme != "file":
                        self.headers = {};
                        noOfHeaders = int(input("Number of Headers you want to add:"))
                        for i in range(noOfHeaders):
                            header = input("Enter your header")
                            value = input("Enter your header's value")
                            self.headers[header] = value
        except:
            self.type == url.split(":", 1)

    # Initializing a socket and sending request to the required path
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        if (self.scheme == "https"):
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect((self.host, self.port))
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        for header, value in self.headers.items():
            request += "{}: {}\r\n".format(header, value)
        request += "Connection: close\r\n"
        request += "\r\n"
        print(request)
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        print("Response is :{}".format(statusline))
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            print("{} : {}".format(header, value))
            response_headers[header.casefold()] = value.strip()
        content = response.read()
        s.close()
        return content
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers


def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
                                 slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


# Formatting the response received and displaying the result from the HTML
def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c;
    if not in_tag and buffer:
        out.append(Text(buffer))
    # finalHtml = html.replace("&lt;", "<").replace("&gt;", ">");
    return out


# def layout(tokens):
#
#     display_list = []
#     weight = "normal"
#     style = "roman"
#     cursor_x, cursor_y = HSTEP, VSTEP
#     for tok in tokens:
#
#     return display_list


def layout_reverse(text):
    display_list = []
    cursor_x, cursor_y = WIDTH - HSTEP * len(text), VSTEP
    for c in text:
        if c == '\n':
            cursor_y += LINE_BREAKS
            continue

        if cursor_x <= 0:
            cursor_y += VSTEP
            cursor_x = WIDTH - HSTEP
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
    return display_list


# A Simple Example Request
# file = "file://C:\Users\tusha\Dummy.txt"
# data = "data:text/html,Hello World!
# filepath = input("enter URL")
# url = Url(filepath)
# url.load(filepath)
# show(url.request())
if __name__ == "__main__":
    import sys

    url = Url(r'data:text/html,<h1 class="title">This is a Centered Title</h1>'
                r'<h1>This is a Regular H1</h1>')
              # r" and something more</center><br><p>a superscrip and something more</p>")
    # url = Url(r"data:text/html,<p>a superscript <sup>sub</sup>"
    #           r" and something more</p>")
    # url = Url(r"https://browser.engineering/text.html")
    # url =    url = Url(r"https://example.com/")
    about = Url("about:blank")
    # try:
    Browser().load(url)
    # finally:
    #     Browser().load(about)
    tkinter.mainloop()
