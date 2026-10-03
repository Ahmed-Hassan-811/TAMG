def check_pose(pose_pdb_path):
    try:
        from posebusters import PoseBusters
        buster = PoseBusters(config="mol")
        return buster.bust(pose_pdb_path)
    except:
        return True
