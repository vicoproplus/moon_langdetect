#!/bin/sh
# tools/c6_zero_network.sh — PID 级零网络运行时断言（FR-24 / NE4-1 / spec §9.4）。
#
# 用法
#   sh tools/c6_zero_network.sh <被测可执行文件> [stdin 文件]
#
#   $1  被测二进制；必须存在且可执行，否则 exit 2
#   $2  作为被测进程的 stdin（默认 /dev/null）；**不得**被当作位置参数忽略
#
# 判据（PID 级，只统计属于被测进程自己的连接）
#   1. `ps -W` 把 Cygwin PID 映射为 WINPID（`ps -W` 第 4 列）；**不得假设
#      二者相等**（实测 ping.exe：$!=14324 而 WINPID=27592）。映射最多重试
#      20 次，每次间隔 50ms。
#   2. WINPID 为空且进程**仍存活** → exit 2（守卫生效）：`awk -v p='' '$NF==p'`
#      会命中空行造成假红，故宁可拒绝判定。
#   3. WINPID 为空且进程**已退出** → 回退 `WINPID=$PID`（瞬时进程分支）。
#   4. 首次 `netstat -ano` 采样在 `kill -0` 循环**之前**执行，保证瞬时进程
#      也满足 SAMPLES >= 1；随后每 0.1s 采样一次并累加 HITS。
#   5. 采样命令：`netstat -ano | awk -v p="$WINPID" '$NF==p' | wc -l`
#      （`netstat -ano` 的 PID 列是**最后一列**，故用 $NF，不写死列号）。
#
# 辅助观察（**不作判据**）
#   全量 `netstat -an | sort` 的前后 diff 只写日志：TIME_WAIT 自然波动
#   （未运行被测程序时 3s/5s/10s 分别新增 5/9/7 行），不可作为判据。
#
# 退出码
#   2  被测二进制缺失 / 不可执行；或 WINPID 映射失败且进程仍存活
#   1  HITS > 0（检测期间存在属于被测 PID 的对外连接）；或子进程退出码非 0
#   0  未发现任何属于被测 PID 的连接，且子进程正常退出
#
# 可移植性：只用 POSIX sh + 相对路径；脚本内不出现任何机器绝对路径。

set -u

EXE=${1:-}
STDIN_FILE=${2:-/dev/null}

# ① 二进制缺失 / 不可执行 → 2
if [ -z "$EXE" ]; then
  exit 2
fi
test -x "$EXE" || exit 2

# 辅助观察：启动前的全量 netstat 快照（不判绿）
SNAP_DIR=$(mktemp -d 2>/dev/null || echo ".")
netstat -an 2>/dev/null | sort > "$SNAP_DIR/before.txt"

# ② 后台启动被测二进制，stdin 来自 $2，stdout/stderr 重定向到 /dev/null
"$EXE" < "$STDIN_FILE" > /dev/null 2>&1 &
CHILD=$!

# ③ Cygwin PID → WINPID 映射（`ps -W` 第 4 列），最多 20 次 × 50ms
WINPID=""
attempt=0
while [ "$attempt" -lt 20 ]; do
  attempt=$((attempt + 1))
  mapped=$(ps -W 2>/dev/null | awk -v q="$CHILD" '$1==q { print $4; exit }')
  if [ -n "$mapped" ]; then
    WINPID=$mapped
    break
  fi
  # 映射不到且进程已退出 → 瞬时进程分支（走回退）
  if ! kill -0 "$CHILD" 2>/dev/null; then
    break
  fi
  sleep 0.05
done

if [ -z "$WINPID" ]; then
  if kill -0 "$CHILD" 2>/dev/null; then
    # `ps -W` 不可用 / 映射失败且进程仍存活 → 拒绝判定（守卫生效）
    kill "$CHILD" 2>/dev/null
    wait "$CHILD" 2>/dev/null
    rm -rf "$SNAP_DIR"
    exit 2
  fi
  # 进程已退出且映射不到 → 回退到 Cygwin PID（瞬时进程）
  WINPID=$CHILD
fi

SAMPLES=0
HITS=0

count_hits() {
  netstat -ano 2>/dev/null | awk -v p="$WINPID" '$NF==p' | wc -l | tr -d ' \t'
}

# ④ 首次采样在 kill -0 循环之前
hits=$(count_hits)
SAMPLES=$((SAMPLES + 1))
HITS=$((HITS + hits))

# 随后每 0.1s 采样一次
while kill -0 "$CHILD" 2>/dev/null; do
  sleep 0.1
  hits=$(count_hits)
  SAMPLES=$((SAMPLES + 1))
  HITS=$((HITS + hits))
done

wait "$CHILD"
CHILD_RC=$?

# 辅助观察：全量 netstat 前后 diff（TIME_WAIT 噪声，不可作为判据）
netstat -an 2>/dev/null | sort > "$SNAP_DIR/after.txt"
ADDED=$(comm -13 "$SNAP_DIR/before.txt" "$SNAP_DIR/after.txt" | wc -l | tr -d ' \t')
REMOVED=$(comm -23 "$SNAP_DIR/before.txt" "$SNAP_DIR/after.txt" | wc -l | tr -d ' \t')
rm -rf "$SNAP_DIR"

printf 'HITS=%s SAMPLES=%s WINPID=%s child_rc=%s\n' "$HITS" "$SAMPLES" "$WINPID" "$CHILD_RC"
printf 'aux_netstat_diff added=%s removed=%s (observation only; TIME_WAIT noise, not a criterion)\n' \
  "$ADDED" "$REMOVED" >&2

# ⑤ 退出码：HITS>0 或子进程 rc≠0 → 1，否则 0
if [ "$HITS" -gt 0 ] || [ "$CHILD_RC" -ne 0 ]; then
  exit 1
fi
exit 0
