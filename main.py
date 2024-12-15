import socket
import ssl
import tkinter as tk
import tkinter.font
from tkinter import Label, Entry, Button


FONTS = {}
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
LINE_BREAKS = 25
SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]

class Text:
    def __init__(self, text,parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    def __init__(self, tag,attributes,parent):
        self.tag = tag
        self.attributes = attributes
        self.children=[]
        self.parent =parent
    
    def __repr__(self):
        return "<" + self.tag + ">"

class HTMLParser:
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]
    def __init__(self,body):
        self.body = body
        self.unfinished =[]
    def get_attributes(self,text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key,value = attrpair.split("=",1)
                if len(value) >2 and value[0] in ["'","\""]:
                    value =value[1:-1]
                attributes[key.casefold()]= value
            else:
                attributes[attrpair.casefold()]= ""
            
        return tag,attributes
    # Handling human error
    def implict_tags(self,tag):
        while True:
            open_tags =  [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head","body","/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")

            elif open_tags == ["html","head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")

            else:
                break
    
    
    
    
    
    
    
    
    
    def add_text(self,text):
        if text.isspace(): return
        self.implict_tags(None)
        parent = self.unfinished[-1];
        node = Text(text,parent)
        parent.children.append(node)

    def add_tag(self,tag):
        tag, attributes = self.get_attributes(tag)
        self.implict_tags(tag)
        if tag.startswith("!"): return
        if tag.startswith("/"):
            if len(self.unfinished)==1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag,parent,attributes)
            self.unfinished.append(node)        
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag,parent,attributes)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) >1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    

    def parse(self):
        text = ""
        in_tag = False
        in_comment = False
        i=0
        while i < len(self.body):
                if in_comment:
                    # Check for the end of a comment
                    if self.body[i:i+3] == "-->":
                        in_comment = False
                        i += 3  # Skip the closing -->
                    else:
                        i += 1  # Continue skipping comment content
                elif self.body[i:i+4] == "<!--":
                    # Start of a comment
                    in_comment = True
                    i += 4  # Skip the opening <!--
                elif self.body[i] == "<":
                    in_tag = True
                    if text: 
                        self.add_text(text)
                    text = ""
                    i += 1
                elif self.body[i] == ">":
                    in_tag = False
                    self.add_tag(text)
                    text = ""
                    i += 1
                else:
                    text += self.body[i]
                    i += 1

            # Handle any remaining text outside tags/comments
        if not in_tag and text:
                self.add_text(text)

        return self.finish()




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
        self.recurse(tokens)
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
        if word.find("&gt;")!=-1:
            word="<"
        if word.find("&lt;")!=-1:
            word=">"
        # word.replace('&lt;','>')
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

    def open_tag(self, tag):
        if tag == "p":
            self.flush()  # End the current paragraph
            self.cursor_y += VSTEP  # Move to a new line for the next paragraph
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "abbr":
            self.weight = "bold"
            self.case = "upper"
        elif tag == "sup":
            self.size = self.size // 2
            self.subscript = True
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "p":
            self.flush()  # End the current paragraph
            self.cursor_y += VSTEP  # Add spacing for the next sibling
        elif tag == "abbr":
            self.weight = "normal"
            self.case = "lower"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "i":
            self.style = "roman"
        elif tag == "big":
            self.size -= 4
        elif tag == "small":
            self.size += 2
        elif tag == "sup":
            self.size = self.size * 2
            self.subscript = False

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        elif tree.tag == "p":
            self.flush()  # Ensure each <p> starts as a sibling
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
        elif tree.tag == "li":
            self.flush()  # Ensure each <li> starts as a sibling
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
            

        



class Browser:
    def __init__(self):
        self.y = 0
        self.x = 0
        self.scroll = 0
        self.nodes = []
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
        nodes = []
       
        print("inside if of load")
        if url.type == "file":
            finalPath = url.filepath.replace("\\", "\\\\")
            f = open(finalPath)
            nodes.append(Text(f.read()))

        elif url.type == "data":
            nodes = HTMLParser(url.html).parse()
        else:
            body = url.request()
            nodes = HTMLParser(body).parse()

        self.display_list = Layout(nodes).display_list
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



# def layout(tokens):
#
#     display_list = []
#     weight = "normal"
#     style = "roman"
#     cursor_x, cursor_y = HSTEP, VSTEP
#     for tok in tokens:
#
#     return display_list
def print_tree(node, indent=0):
        print(" " * indent, node)
        for child in node.children:
            print_tree(child, indent + 2)

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

#     url = Url(r'''data:text/html,<ul>
#   <li>Parent
#   <ul>
#     <li>Child</li>
#   </ul>
# </li>

#               ''')
    #             r'<h1>This is a Regular H1</h1>')
              # r" and something more</center><br><p>a superscrip and something more</p>")
    # url = Url(r"data:text/html,<p>a superscript <sup>sub</sup>"
    #           r" and something more</p>")
    url = Url(r"https://browser.engineering/html.html")
    # url = Url(r"https://example.com/")
    # about = Url("about:blank")
    # try
    # b = Browser()
    # frame = b.window


    Browser().load(url)
    # body = url.request()
    # nodes = HTMLParser(body).parse()
    # print_tree(nodes)
    # finally:
    #     Browser().load(about)
    tkinter.mainloop()


