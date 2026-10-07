# Tracked environment file remediation

Review on 2026-10-07 found that Milestone 1 tracked `.env`. Adding it to
`.gitignore` in the implementation did not untrack the existing file. That also
made the clean-clone quickstart skip its random-secret generation.

The reviewed Milestone 1 file contained placeholder database/cache passwords and
an empty Groq key after parsing comments; no live provider credential was found
in that file. This is not an audit of every historical revision or deployed
credential. If those placeholder passwords were used in a running installation,
replace them and update the actual database/Redis credentials together with the
application configuration. Changing `.env` alone does not change an initialized
Postgres volume's password.

The correction removes `.env` from the tracked tree, retains `.env.example`, and
makes the submission check reject tracked environment files. Fresh clones now
generate random local secrets. Existing developer `.env` files should stay local.

The original file remains in Git history. History has not been rewritten or
force-pushed: coordinate with collaborators and the instructor before any
history cleanup. The assignment's historical `.env` rule is therefore still a
submission issue to disclose; removal at HEAD does not erase earlier commits.
