function chain_log_entry(tag, timestamp, record)
    local prev_sha = read_last_sha()
    local json = require('cjson')
    local entry = json.encode(record)
    local sha256 = require('sha256')
    local chain_input = (prev_sha or "") .. entry
    local chain_sha = sha256.hex(chain_input)
    record["sha_chain"] = chain_sha
    record["prev_sha"] = prev_sha or "GENESIS"
    write_last_sha(chain_sha)
    return 1, timestamp, record
end

-- Helper: read last SHA from file (simple local state)
function read_last_sha()
    local f = io.open("/tmp/flb_last_sha", "r")
    if f then
        local sha = f:read("*l")
        f:close()
        return sha
    end
    return nil
end

function write_last_sha(sha)
    local f = io.open("/tmp/flb_last_sha", "w")
    if f then
        f:write(sha)
        f:close()
    end
end