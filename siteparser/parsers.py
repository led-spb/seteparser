import lxml.cssselect
import lxml.etree
import lxml.html
import base


class SimpleParser(base.SiteParser):
    name = "simple"

    def etree(self, string):
        return lxml.html.fromstring(string)

    def user_context(self):
        response = None
        tree = None

        if self.param('url') is not None:
            # make request
            response = self.make_request()
            # try to parse response as element tree
            tree = None
            try:
                response.encoding = self.param('encoding', 'utf-8')
                tree = self.etree(response.text)
            except StandardError:
                pass
        return {"self": self, "response": response, "tree": tree}

    def parse(self):
        self.items = []

        eval_string = self.param('eval')
        if eval_string is None:
            raise Exception('eval string is None')

        context = self.user_context()
        exec (eval_string, context)
        return self.items


class CssParser(SimpleParser):
    name = "css"

