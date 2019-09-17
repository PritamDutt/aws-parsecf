from aws_parsecf.common import DELETE
from aws_parsecf.conditions import Conditions
from aws_parsecf.functions import Functions
from pprint import pprint as pp
import sys

class Parser:
    def __init__(self, root, default_region, parameters={}):
        self.functions = Functions(self, root, default_region, parameters)
        self.conditions = Conditions(self, root, default_region)

    def explode(self, current):
        # object
        if isinstance(current, dict):
            print(f"current=1============")
            from pprint import pprint as pp
            pp(current)
            print(f"current=1============")

            if '_exploded' in current:
                return
            current['_exploded'] = True
            print(f"current=2============")
            # from pprint import pprint as pp
            pp(current)
            print(f"current=2============")

            # explode children first
            for key, value in current.items():
                print(f"key={key}\tvalue={value}")
                self.exploded(current, key)

            print(f"current=3============")
            # from pprint import pprint as pp
            pp(current)
            print(f"current=3============")

            condition_name = current.get('Condition')
            # added 'unicode' type checking
            # by Alex Ough on July 2nd 2018
            if condition_name and isinstance(condition_name, str):
                # condition
                if not self.conditions.evaluate(condition_name):
                    return DELETE
            # if len(current) == 1 and current.get('Fn::Sub'):
            #     response = self.functions.evaluate('Fn::Sub', current['Fn::Sub'][0])
            elif len(current) == 2: # including '_exploded'
                # possibly a condition
                key, value = next((key, value) for key, value in current.items() if key != '_exploded')
                try:
                    # print(f"sending to evaluate====={key}==={value}")
                    resp = self.functions.evaluate(key, value)
                    # print(f"\n\tevaluate returned======={resp}\n")
                    # if isinstance(resp, list):
                    #     resp = self.functions.evaluate("Fn::Sub", value)
                    #     print(f"\n\tevaluate returned=2======{resp}\n")
                    return resp
                except KeyError as e:
                    if e.args != (key,):
                        raise
                    # not an intrinsic function
                if key != 'Condition': # 'Condition' means a name of a condtion, would make a mess
                    try:
                        return self.conditions.evaluate({key: value})
                    except KeyError as e:
                        if e.args != (key,):
                            raise
                        # not a condition
        # array
        elif isinstance(current, list):
            # print(f"list======{current}")
            for index, value in enumerate(current):
                # print(f"index=={index}__value={value}")
                self.exploded(current, index)

        elif isinstance(current, str):
            pass
            # print(f"\n\n\n\t\t\t\tcurrent is str====={current}\n\n\n\n")

        else:
            pass
            # print(f"\n\n\n\t\t\t\tunmatched=={current}\n\n\n\n")


    def cleanup(self, current):
        if isinstance(current, dict):
            if '_exploded' in current:
                del current['_exploded']
            for key, value in list(current.items()):
                if value is DELETE:
                    del current[key]
                else:
                    self.cleanup(value)
        elif isinstance(current, list):
            deleted = 0
            for index, value in enumerate(list(current)):
                if value is DELETE:
                    del current[index - deleted]
                    deleted += 1
                else:
                    self.cleanup(value)

    def exploded(self, collection, key):
        if collection[key] is None:
            return None
        exploded = self.explode(collection[key])
        if exploded is DELETE:
            # add 'DELETE' attribute with True value
            # instead of overwriting its attributes with "DELETE"
            # to preserve its attributes
            # by Alex Ough on July 2nd 2018
            value = collection[key]
            value['DELETE'] = True
            collection[key] = value
        elif exploded is not None:
            collection[key] = exploded
        return collection[key]
