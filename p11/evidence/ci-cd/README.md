# CI and deployment evidence

**Status: configuration verified; execution blocked by GitLab account identity
verification.**

Merge request !30 created pipeline 3032702793 for commit
`ffb201c77b6c37d46fa12e81942e3778946adaf4`. GitLab marked it failed before any
job was created. Merge request !31 then removed GitLab-hosted runner tags and
routed jobs to eight online ULL group runners (`python` and `node`); pipeline
3032789671 was rejected at the same pre-job stage. Static CI lint accepted
`.gitlab-ci.yml`, while pipeline simulation returned `Identity verification is
required in order to run CI jobs`. This is an external account gate, not a
successful test or deployment result. No paid runner, deployment, or cloud
resource was enabled.

After the account holder completes GitLab's free identity-verification step,
rerun the pipeline and record its job results. A checked-in pipeline definition
and local checks are implementation evidence; they do not establish a successful
GitLab run.
