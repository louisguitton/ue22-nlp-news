terraform {
  backend "remote" {
    organization = "guitton-co"
    workspaces {
      name = "ue22"
    }
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 0.13.7"
}

provider "aws" {
  profile = "default"
  region  = "eu-central-1"
}
