#!/usr/bin/env python

import os 
import sys
import json
from termcolor import colored
import toml
import fire

def get_users(history_path):
    user_path = os.path.join(history_path, "users.json")
    print(f"Loading users from: {user_path=}")
    users = json.load(open(user_path))
    return users

def resolve_user(users, username):
    founduser = None
    for user in users:
        if user["name"] == username:
            founduser = user
            break
        
        if user["id"] == username:
            founduser = user
            break

    print(colored(f"Found the: {founduser['id']=} {founduser['name']=} matches {username=}", "green"))
    return founduser

# def replace_usernames(text, users):
#     newtext = ""
#     for part in text.split(" "):
#         if part[:2] == "<@" and part[-1:] == ">":
#             userid = part[:-1][2:]
#             username = resolve_user(users, userid)["name"]
#             newtext = newtext + f"{username}: "
#         elif part[:2] == "<@" and part[-2:] == ">,": # i'm just copying this use case for now
#             userid = part[:-2][2:]
#             username = resolve_user(users, userid)["name"]
#             newtext = newtext + f"{username} "
#         else:
#             newtext = newtext + f"{part} "

#     return newtext.strip()

def get_chattext(chat, include_user=True):
    if "type" in chat and chat["type"] != "message":
        return None
    
    if "subtype" in chat and chat["subtype"] == "channel_leave":
        return None

    
    if "subtype" in chat and chat["subtype"] == "bot_message":
        return None

    if "text" not in chat:
        return None

    # if "user_profile" not in chat:
        # return None

    # user = chat["user_profile"]
    if "user" not in chat:
        print(colored(f"{chat=}", "red"))
        sys.exit(1)

    if include_user:
        return f"<@{chat['user']}>: {chat['text']}"
    else:
        return chat["text"]
    

def parse_chats(history_path, config, mimicuser, users):
    samples = []
    for root, _, files in os.walk(history_path):
        for file in files:
            channel = os.path.basename(root)
            if "channels" in config and channel not in config["channels"]:
                # print(colored(f"Skipping {channel=} not in {config['channels']=}", "white"))
                continue

            if file.endswith(".json"):
                
                chats = json.load(open(os.path.join(root, file)))
                print(colored(f"Processing: {channel=} {file=} {len(chats)=}", "white"))

                for i, chat in enumerate(chats):
                    if "user" in chat and chat["user"] == mimicuser["id"]:
                        print(f"Mimicing: {chat['user']=} {chat['text']=}")
                        
                        completion = get_chattext(chat, include_user=False)
                        
                        if completion is None:
                            continue # the message wasn't legit text

                        # completion = replace_usernames(completion, users)
                        print(colored(f"Completion: {i=} {completion=}", "yellow"))                   

                        prompt = ""
                        
                        for j in range(i, i - config["num_prev_msgs"], -1):
                            print(f"Currently on {i=}, checking {j=}")
                            if j < 0:
                                print("Skipping negative index")
                                continue
                            if j >= len(chats):
                                print("Skipping out of bounds index")
                                continue

                            if "user" in chats[j] and chats[j]["user"] == mimicuser["id"]:
                                print(f"Skipping {j=} because its the same user {mimicuser['id']=}")
                                continue

                            prev_chat = get_chattext(chats[j], include_user=True)
                            if prev_chat is not None:
                                prompt = f"{prev_chat}\n{prompt}\n"

                        prompt = prompt.strip()
                        if prompt == "":
                            prompt = config["noprevtoken"]
                            
                        # prompt = replace_usernames(prompt, users)
                        print(colored(f"Prompt: {i-1=} {prompt=}", "cyan"))

                        if config["inc_channel_name"]:
                            prompt = f"[{channel}]\n" + prompt

                        samples.append({
                            "prompt": prompt + f"\n<@{mimicuser['id']}>:",
                            "completion": f" {completion} {config['endtoken']}"
                        })
    return samples

def write_samples(samples, config):

    # remove duplicates
    print(f"Samples has length of {len(samples)=}")
    # deduped_samples = [i for n,i in enumerate(samples) if i not in samples[n+1:]]
    deduped_samples = {frozenset(item.items()) : item for item in samples}.values()
    print(f"Deduped Samples has length of {len(deduped_samples)=}")

    f = open(config["output_path"], "w")
    for sample in deduped_samples:
        jsonstr = json.dumps(sample)
        f.write(jsonstr + "\n")
    
    f.close()
    print(colored(f"Wrote {len(deduped_samples)} samples to {config['output_path']=}", "green"))


def main(config_path="config.toml"):
    config = toml.load(config_path)["config"]

    history_path = config["history_path"]
    print(f"History path: {history_path=}")
    users = get_users(history_path)
    mimicuser = resolve_user(users, config["user"])
    samples = parse_chats(history_path, config, mimicuser, users)
    print(f"Found {len(samples)=} samples")

    for sample in samples[:10]:
        print(f"{sample=}")

    write_samples(samples, config)

if __name__ == "__main__":
    fire.Fire(main)