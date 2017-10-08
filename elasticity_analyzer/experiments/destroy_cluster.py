from elasticity_analyzer.do_base import DOBase, wait_until_done


class DestroyCluster(DOBase):
    def run(self):
        droplets = self.get_droplet_group()

        self.destroy_all()
        wait_until_done(droplets)
        print('destroyed')


if __name__ == "__main__":
    DestroyCluster().start()
