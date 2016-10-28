#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
"""
Plugin purpose
==============

- clone (with option mirror) a list of git repo in a folder (same auth for all)
- create a unique tar.xz archive with all repo inside

************** IMPORTANT NOTE ********************************************
This script is not yet finished, it only support a backup from a
"ssh access with key-auth" for all git repo. Feel free to improve it !
**************************************************************************

@author: Kévin Burgi <kbu at kbulabs dot fr>
@copyright: (C) 2016 kbu
@license: GPL(v3)
/*
 ****************************************************************************
 *  Copyright (c) 2016 Kévin Burgi <kbu at kbulabs dot fr>                  *
 *                                                                          *
 *  This script is free software: you can redistribute it and/or modify     *
 *  it under the terms of the GNU General Public License as published by    *
 *  the Free Software Foundation, either version 3 of the License, or       *
 *  (at your option) any later version.                                     *
 *                                                                          *
 *  This script is distributed in the hope that it will be useful,          *
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
 *  GNU General Public License for more details.                            *
 *                                                                          *
 *  You should have received a copy of the GNU General Public License       *
 *  along with this script.  If not, see <http://www.gnu.org/licenses/>.        *
 ****************************************************************************
*/
"""

############### CONFIG #####################
# name of target folder where backup will be stored
BACKUP_TO_LOCAL_FOLDER="/tmp/bk_git_repo/" 

# auth param. to your git
USE_CREDENTIALS = True    # always TRUE 
CRED_USER = "git"         # gitlab use git !!
CRED_SSHKEY_PRIV = "/home/user/.ssh/id_dsa"
CRED_SSHKEY_PUB = "/home/user/.ssh/id_dsa.pub"

CREATE_TAR_XZ=True # Create an archive with all repo ?

############ LIST REMOTE REPO ##############
REPO = {
        "myrepo.git":'git@my.githost.fr:foo/myrepo.git',
        "myrepo2.git":'git@my.githost.fr:foo/myrepo2.git',
}
 
########### DEVELOPPER PART ################
version="0.1"

############################################
############################################
############################################

import sys
import os
import shutil
import pygit2
from contextlib import contextmanager
import time
import tarfile

                
class GitRepo():
    """ Create a git repo object with his own config """
    def __init__(self, repo, credentials=None):
        """ NOTE : repo muste be a list ['name', 'url'] with
            - name : the bakcup name of the repo
            - url : the url of the depot
        """
        d = dict()
        d['name'] = repo[0]
        d['url'] = repo[1]
        self.repo = d
        self.use_credentials = USE_CREDENTIALS
        self._ssh_user = CRED_USER
        self._ssh_key_priv = CRED_SSHKEY_PRIV
        self._ssh_key_pub = CRED_SSHKEY_PUB
        self.credentials_callbacks = None
        self.displayRepoGitlab()

    def displayRepoGitlab(self):
        """ Display the current repo config """
        print("\t--------------------------------------------------------------")
        print("\t| A repo has been configured :")
        print("\t|\t{:10s} - {}".format(self.repo['name'], self.repo['url']))
        if self.use_credentials == True:
            print("\t|\t => Credentials info used for previously listed git repo : ")
            print("\t|\t         User : {}".format(self.ssh_user))
            print("\t|\t         SSH pub key : {}".format(self.ssh_key_pub))
            print("\t|\t         SSH priv key : {}".format(self.ssh_key_priv))
        print("\t--------------------------------------------------------------")


    def init_remote(repo, name, url):
        # Create the remote with a mirroring url
        remote = repo.remotes.create(name, url, "+refs/*:refs/*")
        # And set the configuration option to true for the push command
        mirror_var = "remote.{}.mirror".format(name)
        repo.config[mirror_var] = True
        # Return the remote, which pygit2 will use to perform the clone
        return remote

    def init_credentials(self):
        ssh_cred = pygit2.Keypair(self.ssh_user, 
                                  self.ssh_key_pub,
                                  self.ssh_key_priv, 
                                  "")    
        self.credentials_callbacks = pygit2.RemoteCallbacks(credentials=ssh_cred)

    @contextmanager 
    def mirror_repo(self, local_path):
        path="./"
        if local_path is not None:
            path = local_path

        prevdir = os.getcwd()
        os.chdir(os.path.expanduser(path))
        
        try:                
            if self.use_credentials == True:
                self.init_credentials()
                pygit2.clone_repository(self.repo['url'], self.repo['name'] ,
                                        remote=GitRepo.init_remote,
                                        callbacks=self.credentials_callbacks)
            else:
                pygit2.clone_repository(self.repo['url'], self.repo['name'] ,
                                        remote=self.init_remote)
        finally:
            os.chdir(prevdir)

    def _get_ssh_user(self):
        return self._ssh_user

    def _get_ssh_key_priv(self):
        return self._ssh_key_priv

    def _get_ssh_key_pub(self):
        return self._ssh_key_pub

    ssh_user = property(_get_ssh_user)
    ssh_key_priv = property(_get_ssh_key_priv)
    ssh_key_pub = property(_get_ssh_key_pub)


class BackupAllGitRepoToLocalFolder():
    """ 
        Main Class - backup all listed repo
        
        Warning : only ssh credentials yet supported !!!
    """
    def __init__(self):       
        if BACKUP_TO_LOCAL_FOLDER is None:
            self.targetPath="./bk_default"
        else:
            self.targetPath=BACKUP_TO_LOCAL_FOLDER
        
        self.targetPathOld=self.targetPath.rstrip('/') + ".old"
        #print("Old path is {}".format(self.targetPathOld))

        print(">> Preparing the list of repo")
        grepos = []
        for repoName,repoURL in REPO.items():
            #print("repoName => {}    \t {}".format(repoName,repoURL))
            curRepo=[repoName, repoURL]
            gr = GitRepo(curRepo)
            grepos.append(gr)
        self.repos = grepos
        print("\n>> {} repo added in the queue.".format(len(self.repos)))


    def goBaby(self):
        # check if folder exist and if not, create it (>python3.2)
        if os.path.exists(self.targetPath):
           self.processOldFolder()
    
        print(">> Create the target folder {}".format(self.targetPath))
        os.makedirs(self.targetPath, exist_ok=True) # to put in try bloc                   

        #repo = [self.repos[0],]  # just for test purpose
        #for curGit in repo:
        for curGit in self.repos:
            git_name = curGit.repo['name']
            git_url = curGit.repo['url']
            print(">> Backing up repo \"{}\" -  URL {}".format(git_name, git_url))            
            curGit.mirror_repo(self.targetPath)
        self.createFileWithDatetime()

        if CREATE_TAR_XZ is True:
            self.make_tar()


    def processOldFolder(self):
        print(">> The target folder already exists from previous mirror")
        print(">> Move {} to {} (remove the old folder if already exists)"
                .format(self.targetPath, self.targetPathOld))
        if os.path.exists(self.targetPathOld):
            try:
                    shutil.rmtree(self.targetPathOld)
            except OSError as e:
                    print ("Error: %s - %s." % (e.filename,e.strerror))
        
        # now move target to target.old
        shutil.move(self.targetPath, self.targetPathOld)


    def createFileWithDatetime(self):
        print(">> Writing a file with current date in target_folder")
        curDate=time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        full_path=self.targetPath +"/"+curDate+".txt"
        f = open(full_path, 'w')
        f.write("This is an automatic backup [date : {}]\n".format(curDate))
        f.close

    @contextmanager 
    def make_tar(self):
        print(">> Creating a tar.xz archive will all git-backup")
        prevdir = os.getcwd()

        # go in the parent directory of the targetPath
        path = self.targetPath.rstrip('/')  #remove last "/"
        path = path.split('/')
        path = path[:-1]                    
        path = "/".join(path)
        
        #getting the date (will prefix the tar filename)
        prefix_date = time.strftime("%Y-%m-%d")
        outfilename = prefix_date + "_git_repo_backup.tar.xz"
        full_path = path + "/" + outfilename

        os.chdir(os.path.expanduser(path))
        try:   
            tar = tarfile.open(outfilename, "w:xz")
            tar.add(self.targetPath)
            tar.close()
            print(">> Tar archive successfully created")
            print(">> Where is it ? Here : {}".format(full_path))
        finally:
            os.chdir(prevdir)
        

if __name__ == "__main__":
    print("\n>>##########################################")
    print(">>       BACKUP A REMOTE GIT REPO             ")
    print(">>      (ssh key access required !)           ")
    print(">>    ----------------------------------      ")
    print(">>             version : {}".format(version))
    #print("* name {}".format(sys.argv[0]))
    print("\n>>##########################################")
    
    mygit = BackupAllGitRepoToLocalFolder()
    mygit.goBaby()

    print("\n>> End of script - Have a nice day :-)")
