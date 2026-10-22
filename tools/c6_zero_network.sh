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
#      二者相等**（实测 ping.exe：$!=14324 而 WINPID=27592）。映射预算按
#      **墙钟截止时间**（2s，自启动起算）而不是尝试次数：每次 `ps -W` 本身
#      约 150ms，旧的「20 次 × 50ms」实测约 3.1s，且会让中途退出的子进程
#      走进回退分支（见 3.(d)）。
#   2. 映射期间用 `OBSERVED_ALIVE` 记录是否**曾经**观察到子进程存活
#      （`kill -0` 成功）。
#   3. 归属判定（三路 + 拒绝判定）：
#      (a) WINPID 非空 → 正常路径，判 HITS；
#      (b) WINPID 空且进程**仍存活** → exit 2（守卫生效）：`awk -v p='' '$NF==p'`
#          会命中空行造成假红，故宁可拒绝判定；
#      (c) WINPID 空、进程已退出、且 `OBSERVED_ALIVE=0` → 合法瞬时进程，
#          回退 `WINPID=$CHILD` 并判 HITS（保留五态表态 ④ rc=0）；
#      (d) WINPID 空、进程已退出、但 `OBSERVED_ALIVE=1` → **无法归属连接**，
#          打印 `c6: WINPID unmapped while child was alive; refusing to judge`
#          并 exit 2。Cygwin PID 永不出现在 `netstat -ano` 的 PID 列里，回退
#          到 `$CHILD` 会让 HITS 结构性恒为 0（与网络活动无关的假绿）。
#   4. **netstat 可用性正控（I1）**：首次采样之后，若 `netstat -ano` 输出
#      行数 <= 1（netstat 缺失 / shim 退出 127 / 无 socket 能力），则
#      `HITS=0` 是空集假绿；此时打印 `c6: netstat unavailable ...` 并 exit 2。
#   5. 首次 `netstat -ano` 采样在 `kill -0` 循环**之前**执行，保证瞬时进程
#      也满足 SAMPLES >= 1；随后每 0.1s 采样一次。
#   6. 采样命令：`netstat -ano | awk -v p="$WINPID" '$NF==p' | wc -l`
#      （`netstat -ano` 的 PID 列是**最后一列**，故用 $NF，不写死列号）。
#      **HITS 语义**：HITS 是**逐次采样行数的累加和**（per-sample sum），
#      **不是连接条数** —— 同一条连接会在多帧采样中被重复计入。
#
# 辅助观察（**不作判据**）
#   全量 `netstat -an | sort` 的前后 diff 只写日志：TIME_WAIT 自然波动
#   （未运行被测程序时 3s/5s/10s 分别新增 5/9/7 行），不可作为判据。
#   `mktemp -d` 失败时**整段跳过**该辅助观察（不回退到 `.`，避免污染 CWD）。
#
# 退出码
#   2  被测二进制缺失 / 不可执行；netstat 不可用；或 WINPID 归属失败
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

# 辅助观察：启动前的全量 netstat 快照（不判绿）；mktemp 失败则整段跳过
SNAP_DIR=$(mktemp -d 2>/dev/null) || SNAP_DIR=""
if [ -n "$SNAP_DIR" ]; then
  netstat -an 2>/dev/null | sort > "$SNAP_DIR/before.txt"
fi

cleanup_snap() {
  if [ -n "$SNAP_DIR" ]; then
    rm -rf "$SNAP_DIR"
  fi
}

# ② 后台启动被测二进制，stdin 来自 $2，stdout/stderr 重定向到 /dev/null
"$EXE" < "$STDIN_FILE" > /dev/null 2>&1 &
CHILD=$!

# 墙钟毫秒；`date +%s%N` 不可用时返回空串（触发尝试次数兜底预算）
now_ms() {
  _t=$(date +%s%N 2>/dev/null)
  case "$_t" in
    '' | *[!0-9]*) printf '%s' "" ;;
    *) printf '%s' "$((_t / 1000000))" ;;
  esac
}

MAP_BUDGET_MS=2000
START_MS=$(now_ms)
DEADLINE_MS=""
if [ -n "$START_MS" ]; then
  DEADLINE_MS=$((START_MS + MAP_BUDGET_MS))
fi

# ③ Cygwin PID → WINPID 映射（`ps -W` 第 4 列）；墙钟预算 MAP_BUDGET_MS
WINPID=""
OBSERVED_ALIVE=0
attempt=0
while :; do
  mapped=$(ps -W 2>/dev/null | awk -v q="$CHILD" '$1==q { print $4; exit }')
  if [ -n "$mapped" ]; then
    WINPID=$mapped
    break
  fi
  if kill -0 "$CHILD" 2>/dev/null; then
    OBSERVED_ALIVE=1
  else
    break
  fi
  if [ -n "$DEADLINE_MS" ]; then
    _now=$(now_ms)
    if [ -n "$_now" ] && [ "$_now" -ge "$DEADLINE_MS" ]; then
      break
    fi
  else
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 40 ]; then
      break
    fi
  fi
  sleep 0.05
done

if [ -z "$WINPID" ]; then
  if kill -0 "$CHILD" 2>/dev/null; then
    # (b) 映射失败且进程仍存活 → 拒绝判定（守卫生效）
    OBSERVED_ALIVE=1
    printf '%s\n' 'c6: WINPID unmapped while child is still alive; refusing to judge' >&2
    kill "$CHILD" 2>/dev/null
    wait "$CHILD" 2>/dev/null
    cleanup_snap
    exit 2
  fi
  if [ "$OBSERVED_ALIVE" -eq 1 ]; then
    # (d) 进程曾在运行期存活却始终没映射到 WINPID → 无法归属连接
    wait "$CHILD" 2>/dev/null
    printf '%s\n' 'c6: WINPID unmapped while child was alive; refusing to judge' >&2
    cleanup_snap
    exit 2
  fi
  # (c) 从未观察到存活且已退出 → 合法瞬时进程，回退到 Cygwin PID
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

# ④b netstat 可用性正控（I1）：空集不得被当作「零连接」
NETSTAT_ROWS=$(netstat -ano 2>/dev/null | wc -l | tr -d ' \t')
if [ "${NETSTAT_ROWS:-0}" -le 1 ]; then
  printf 'c6: netstat unavailable (netstat -ano produced %s line(s); HITS=0 would be a vacuous pass)\n' \
    "${NETSTAT_ROWS:-0}" >&2
  if kill -0 "$CHILD" 2>/dev/null; then
    kill "$CHILD" 2>/dev/null
  fi
  wait "$CHILD" 2>/dev/null
  cleanup_snap
  exit 2
fi

# 随后每 0.1s 采样一次（HITS = per-sample 行数累加和，非连接条数）
while kill -0 "$CHILD" 2>/dev/null; do
  sleep 0.1
  hits=$(count_hits)
  SAMPLES=$((SAMPLES + 1))
  HITS=$((HITS + hits))
done

wait "$CHILD"
CHILD_RC=$?

# 辅助观察：全量 netstat 前后 diff（TIME_WAIT 噪声，不可作为判据）
ADDED=0
REMOVED=0
if [ -n "$SNAP_DIR" ]; then
  netstat -an 2>/dev/null | sort > "$SNAP_DIR/after.txt"
  ADDED=$(comm -13 "$SNAP_DIR/before.txt" "$SNAP_DIR/after.txt" | wc -l | tr -d ' \t')
  REMOVED=$(comm -23 "$SNAP_DIR/before.txt" "$SNAP_DIR/after.txt" | wc -l | tr -d ' \t')
  cleanup_snap
fi

printf 'HITS=%s SAMPLES=%s WINPID=%s child_rc=%s\n' "$HITS" "$SAMPLES" "$WINPID" "$CHILD_RC"
if [ -n "$SNAP_DIR" ]; then
  printf 'aux_netstat_diff added=%s removed=%s (observation only; TIME_WAIT noise, not a criterion)\n' \
    "$ADDED" "$REMOVED" >&2
else
  printf '%s\n' 'aux_netstat_diff skipped (mktemp -d unavailable)' >&2
fi
# ⑤ 退出码：HITS>0 或子进程 rc≠0 → 1，否则 0
if [ "$HITS" -gt 0 ] || [ "$CHILD_RC" -ne 0 ]; then
  exit 1
fi
exit 0
