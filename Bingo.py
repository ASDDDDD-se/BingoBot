import discord
from discord.ext import commands
import numpy as np
import pandas as pd
import random
import os

# 환경 변수에서 디스코드 토큰 불러오기
TOKEN = os.getenv("DISCORD_TOKEN")

# 빙고판 생성 (1부터 25까지 순차 배치)
bingo_board = np.arange(1, 26).reshape(5, 5)

# 확률 계산을 위한 시뮬레이션 함수
def calculate_probabilities(selected_numbers, remaining_numbers, attempts_left, simulations=5000):
    success_counts = {num: 0 for num in remaining_numbers}
    remaining_list = sorted(remaining_numbers)
    
    for _ in range(simulations):
        for num in remaining_numbers:
            possible_choices = [n for n in remaining_list if n != num]
            
            if len(possible_choices) >= attempts_left:
                random_selection = set(random.sample(possible_choices, attempts_left))
            else:
                random_selection = set(possible_choices)
            
            test_selection = selected_numbers | {num} | random_selection
            if count_bingo_lines(test_selection) >= 4:
                success_counts[num] += 1
    
    return {num: (success_counts[num] / simulations) * 100 if simulations > 0 else 0 for num in success_counts}

# 4줄 빙고 계산 함수
def count_bingo_lines(selected):
    bingo_count = 0
    selected_set = set(selected)
    
    for row in bingo_board:
        if set(row).issubset(selected_set):
            bingo_count += 1
    
    for col in bingo_board.T:
        if set(col).issubset(selected_set):
            bingo_count += 1
    
    diag1 = set(np.diag(bingo_board))
    diag2 = set(np.diag(np.fliplr(bingo_board)))
    if diag1.issubset(selected_set):
        bingo_count += 1
    if diag2.issubset(selected_set):
        bingo_count += 1
    
    return bingo_count

# 디스코드 봇 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# 게임 상태 저장
selected_numbers = set()
attempts_left = 16
remaining_numbers = set(range(1, 26))
probabilities = {num: 0 for num in range(1, 26)}

# 숫자 선택 명령어
@bot.command()
async def select(ctx, *numbers: int):
    global selected_numbers, attempts_left, remaining_numbers, probabilities
    
    if attempts_left <= 0:
        await ctx.send("❌ 기회가 모두 소진되었습니다. !reset 명령어를 사용해 게임을 초기화하세요.")
        return
    
    for num in numbers:
        if num in selected_numbers:
            await ctx.send(f"⚠️ {num}은 이미 선택된 숫자입니다.")
            continue
        if num not in remaining_numbers:
            await ctx.send(f"❌ {num}은 선택할 수 없는 숫자입니다.")
            continue
        
        selected_numbers.add(num)
        remaining_numbers.remove(num)
        attempts_left -= 1
    
    probabilities = calculate_probabilities(selected_numbers, remaining_numbers, attempts_left)
    max_prob = max(probabilities.values(), default=0)
    max_prob_numbers = [num for num, prob in probabilities.items() if prob == max_prob and max_prob > 0]
    
    # 빙고판 출력
    bingo_msg = "**빙고판**\n"
    for r in range(5):
        for c in range(5):
            num = bingo_board[r, c]
            if num in selected_numbers:
                bingo_msg += "❌ "
            elif num in max_prob_numbers:
                bingo_msg += f"**{num} ({probabilities[num]:.1f}%)** "
            else:
                bingo_msg += f"{num} ({probabilities[num]:.1f}%) "
        bingo_msg += "\n"
    
    await ctx.send(bingo_msg)
    await ctx.send(f"🎯 남은 기회: {attempts_left} | 현재 빙고 개수: {count_bingo_lines(selected_numbers)}")

# 리셋 명령어
@bot.command()
async def reset(ctx):
    global selected_numbers, attempts_left, remaining_numbers, probabilities
    
    selected_numbers.clear()
    remaining_numbers = set(range(1, 26))
    attempts_left = 16
    probabilities = {num: 0 for num in range(1, 26)}
    
    await ctx.send("🔄 게임이 초기화되었습니다. !select 명령어로 숫자를 선택하세요!")

# 봇 실행
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
