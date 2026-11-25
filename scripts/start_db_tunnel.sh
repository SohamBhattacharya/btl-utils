#!/usr/bin/env bash

set -u

SOCKET_PATH="$HOME/.ssh/socket_db_tunnel"
REMOTE_HOST="lxplus.cern.ch"
SSH_USER=""
RESTART=false
STATUS=false
CLOSE=false

usage() {
    echo "Usage: $0 [--user USER] [--restart] [--status] [--close]" >&2
    echo "       $0 <lxplus username>" >&2
    echo "" >&2
    echo "Manage the SSH tunnel to dbloader-mtd.cern.ch:8113." >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --user USER   lxplus SSH username (can also be passed positionally)" >&2
    echo "  --restart     Close and reopen the tunnel" >&2
    echo "  --status      Just check the status of the tunnel and exit" >&2
    echo "  --close       Close the tunnel and exit" >&2
    echo "  -h, --help    Show this help" >&2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user)
            if [[ $# -lt 2 ]]; then
                echo "Error: --user requires a value." >&2
                usage
                exit 1
            fi
            SSH_USER="$2"
            shift 2
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        --status)
            STATUS=true
            shift
            ;;
        --close)
            CLOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Error: unknown argument: $1" >&2
            usage
            exit 1
            ;;
        *)
            if [[ -n "$SSH_USER" ]]; then
                echo "Error: username specified more than once." >&2
                usage
                exit 1
            fi
            SSH_USER="$1"
            shift
            ;;
    esac
done

check_tunnel() {
    [[ -S "$SOCKET_PATH" ]] &&
        ssh -S "$SOCKET_PATH" -O check "$REMOTE_HOST" >/dev/null 2>&1
}

report_status() {
    if check_tunnel; then
        echo "Database tunnel: OK"
        return 0
    fi

    echo "Database tunnel: NOT OPEN"
    return 1
}

close_tunnel() {
    if [[ -S "$SOCKET_PATH" ]]; then
        ssh -S "$SOCKET_PATH" -O exit "$REMOTE_HOST" >/dev/null 2>&1 || true
    fi
    rm -f "$SOCKET_PATH"
}

if [[ "$STATUS" == true ]]; then
    report_status
    exit 0
fi

if [[ "$CLOSE" == true ]]; then
    close_tunnel
    echo "Database tunnel closed."
    exit 0
fi

if [[ "$RESTART" == false ]] && report_status; then
    exit 0
fi

if [[ -z "$SSH_USER" ]]; then
    echo "Error: lxplus username is required to start the tunnel." >&2
    usage
    exit 1
fi

close_tunnel
mkdir -p "$HOME/.ssh"

echo "Opening database tunnel as ${SSH_USER}@${REMOTE_HOST} ..."
if ! ssh -f -N -M -S "$SOCKET_PATH" \
    -o ExitOnForwardFailure=yes \
    -L 8113:dbloader-mtd.cern.ch:8113 \
    "${SSH_USER}@${REMOTE_HOST}"; then
    echo "Failed to open database tunnel." >&2
    exit 1
fi

if ! check_tunnel; then
    echo "Database tunnel setup failed." >&2
    exit 1
fi

echo "Database tunnel is ready:"
echo "  localhost:8113 -> dbloader-mtd.cern.ch:8113"
