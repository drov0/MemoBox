from steem import *
from websocket import create_connection
import base64


class MemoBox:

    active_key = ""
    account = ""
    steem = None
    node = None
    def __init__(self, active_key, username, node="wss://steemd-int.steemit.com"):
        self.active_key = active_key
        self.node = create_connection(node)
        self.steem = Steem(node=self.node, keys=active_key)
        self.account = username

    def sendfile(self, filename, reciever):
        with  open(filename, 'rb') as f:
            data = base64.b64encode(f.read())

        blocks_needed = ((data.__len__() - 1) // 2048) + 1

        if (blocks_needed >= 100):
            return False # let's not overload the chain for now

        sent = 0
        ids = []
        while (sent != data.__len__()):
            to_send = data[:2040]
            data = data[2040:] # remove what we already sent
            to_send = to_send.decode(encoding='UTF-8')
            id = self.send(self.account, to_send)
            ids.append(id[0][0])

        header = filename + ":"
        header += ":".join(str(x) for x in ids)

        self.send(self.account, header)

        return True

    def get_memo_by_id(self, id):
        return self.get_memo(self.steem.get_account_history(self.account, id, 0))[0]

    def send(self, reciever, data):
            self.steem.transfer(reciever, 0.001, asset="SBD", account=self.account, memo=data)
            return self.retrieve(recent=1, step=50)

    def retrieve(self, keyword="", position=-1, keyword_and_account=False,
                 recent=1, step=10000, minblock=-1, remove_keyword=True):
        memo_list = []
        if position > -1:
            # This returns the memo based on a saved position
            return self.get_memo(self.steem.get_account_history(self.account, position, 1))
        else:
            # If the first is 0, it checks the first one with the keyword or account
            # (or and depending on keyword and account)
            found = True
            memo_list = []
            # This gets the total amount of items in the accounts history
            # This it to prevent errors related to going before the creation of the account
            size = self.steem.get_account_history(self.account, -1, 0)[0][0]
            # print(size)
            position = size

            if position < 0:
                position = step + 1
            while found:
                # Checks if the

                if recent > 0 and len(memo_list) > 0:
                    if len(memo_list) >= recent:
                        break
                history = self.steem.get_account_history(self.account, position, step)
                memos = self.get_memo(history)
                has_min_block = False
                for i in range(len(memos) - 1, -1, -1):
                    if len(memo_list) >= recent:
                        break
                    has_keyword = False

                    if memos[i][3] < minblock:
                        has_min_block = True
                    if keyword != "":
                        memos[i][2].split(keyword)
                        if type(memos[i][2]) == list:
                            for seg in memos[i][2]:
                                if seg != keyword and remove_keyword:
                                    memos[i][2] += seg
                            has_keyword = True
                    has_account = memos[i][1] == self.account

                    if keyword_and_account:
                        if has_keyword and has_account:
                            memo_list.append(memos[i])
                    else:
                        if has_account or has_keyword:
                            memo_list.append(memos[i])
                if position == step + 1 or has_min_block:
                    break
                elif position - step <= step:
                    position = step + 1
                else:
                    position -= step
            return memo_list
            # This checks if it has the keyword or is by the account

    def get_memo(self, history_list):
        memos = []
        for i in history_list:
            memo = []
            for ii in i:

                if type(ii) == dict:
                    try:

                        if ii['op'][0] == 'transfer':
                            memo.append(ii['op'][1]['from'])
                            memo.append(ii['op'][1]['memo'])
                            memo.append(ii['block'])
                            memos.append(memo)

                        else:
                            memo = []
                    except:
                        pass
                if type(ii) == int:
                    memo.append(ii)
        return memos

    def get_file(self, filename, save_to):
        header = self.retrieve(recent=1, step=150, keyword=filename)[0][2]

        memos = header[filename.__len__()+1:].split(":")

        data = ""

        for m in memos :
            data += self.get_memo_by_id(m)[2]

        fh = open(save_to, "wb")
        fh.write(base64.b64decode(data))
        fh.close()