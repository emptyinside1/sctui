{
  description = "A TUI SoundCloud player";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3Packages;

        sc-tui-deps = with pythonPackages; [
          textual
          yt-dlp
          python-mpv
          platformdirs
        ];

        native-deps = with pkgs; [
          mpv
          ffmpeg
        ];
      in {
        packages.default = pythonPackages.buildPythonApplication {
          pname = "sc-tui";
          version = "0.1.0";

          format = "pyproject";

          src = ./.;

          propagatedBuildInputs = sc-tui-deps;

          # NixOS specific: passing LD_LIBRARY_PATH for python-mpv
          makeWrapperArgs = [
            "--prefix LD_LIBRARY_PATH : ${pkgs.lib.makeLibraryPath native-deps}"
            "--prefix PATH : ${pkgs.lib.makeBinPath native-deps}"
          ];

          meta = with pkgs.lib; {
            description = "Terminal User Interface for SoundCloud";
            license = licenses.mit;
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            (pkgs.python3.withPackages (ps: with ps; [
              textual
              yt-dlp
              python-mpv
              platformdirs
            ]))
          ] ++ native-deps;

          LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath native-deps}";
        };
      }
    );
}
