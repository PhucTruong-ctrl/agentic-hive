{
  lib,
  stdenvNoCC,
  makeWrapper,
  bash,
  coreutils,
  util-linux,
  gnused,
  gawk,
  gnugrep,
  jq,
  ripgrep,
  git,
  tmux,
}:

stdenvNoCC.mkDerivation {
  pname = "agentic-hive";
  version = "0.1.0";

  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../bin
      ../share
    ];
  };

  nativeBuildInputs = [ makeWrapper ];
  buildInputs = [ bash ];

  installPhase = ''
    runHook preInstall
    install -Dm755 -t $out/bin bin/hive bin/hive-hook bin/hive-launch bin/hive-dash
    install -Dm644 -t $out/share/agentic-hive share/member-instruction.md
    patchShebangs $out/bin
    for f in $out/bin/*; do
      wrapProgram "$f" \
        --prefix PATH : "$out/bin:${
          lib.makeBinPath [
            coreutils
            util-linux
            gnused
            gawk
            gnugrep
            jq
            ripgrep
            git
            tmux
          ]
        }" \
        --set-default HIVE_SHARE "$out/share/agentic-hive"
    done
    runHook postInstall
  '';

  meta = {
    description = "Agentic Hive Core: a shared Unix habitat for persistent coding agents";
    mainProgram = "hive";
    platforms = lib.platforms.linux;
  };
}
