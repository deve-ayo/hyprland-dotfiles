# Animfetch: exibir apenas frame estático (--once) no terminal puro
if [[ -t 1 && $- == *i* && $SHLVL -le 1 && -z "$HARNESS" && -z "$CI" && ${LINES:-24} -ge 24 ]]; then
    command -v animfetch >/dev/null && animfetch --once
fi

alias cat-once='animfetch --once'
alias cat-run='animfetch --play'
alias cat-unpin='animfetch --unpin'
