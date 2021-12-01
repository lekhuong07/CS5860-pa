import docx2txt  # only works for docx


def open_brackets_helper(input_string):
    ct = 0
    for s in input_string:
        if s == '{':
            ct += 1
    if ct >= 2:
        return input_string.split('{')
    return [input_string]


class ProgParser:
    def __init__(self, path):
        self.text = docx2txt.process(path)  # "testing.docx"
        self.cleaned_text = [t.strip() for t in self.text.split('\n') if t != '']

    def get_all_programs(self):
        mapping = {}
        curr = ''
        for ct in self.cleaned_text:
            if ct.startswith("Program"):
                curr = ct
                mapping[curr] = []
            else:
                if curr != '':
                    mapping[curr].append(ct)
        for m, v in mapping.items():
            new_value = []
            i = 0
            cob = open_brackets_helper(v)
            for c in cob:
                while i < len(c):
                    res = c[i][0].lower() + c[i][1:]
                    temp = str(res)
                    new_value.append(temp)
                    i += 1
            mapping[m] = new_value

        return mapping


if __name__ == "__main__":
    test_path = "testing.docx"
    pp = ProgParser(test_path)
