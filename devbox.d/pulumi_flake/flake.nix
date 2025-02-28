{
  description = "A flake that outputs Pulumi";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # Define a map that translates Nix system names to Pulumi system names
        pulumiSystemMap = {
          "x86_64-linux" = "linux-x64";
          "aarch64-linux" = "linux-arm64";
          "x86_64-darwin" = "darwin-x64";
          "aarch64-darwin" = "darwin-arm64";
          "x86_64-windows" = "windows-x64";
          "aarch64-windows" = "windows-arm64";
        };

        # Get the Pulumi system name from the map using the current system
        pulumiSystem = pulumiSystemMap.${system};

        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              pulumi = prev.stdenv.mkDerivation rec {
                pname = "pulumi";
                version = "3.132.0";
                src = prev.fetchurl {
                  url = "https://github.com/pulumi/pulumi/releases/download/v${version}/pulumi-v${version}-${pulumiSystem}.tar.gz";
                  sha256 = "0wkmc2kajcd35js6ircf5an7h3hq7ra8z154v47dyid39m7c5bc5";
                };
                nativeBuildInputs = [ prev.makeWrapper ];
                installPhase = ''
                  mkdir -p $out/bin
                  cp -r * $out/bin/
                '';
              };
            })
          ];
        };
      in
      {
        packages.default = pkgs.pulumi;
      });
}
